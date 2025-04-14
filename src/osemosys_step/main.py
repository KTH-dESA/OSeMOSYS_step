"""Main entry point for the script

The main function of main_ms takes always three inputs and can take the optional
input solver. The three needed inputs are the path to the datafile of the model,
the step length - either an integer in case the step length is always the same
or a list of two integers, the first indicating the length of the first step and
the second of the remaining steps - and the path to the folder with the csv files
containing the data for the parameter to varied between scenarios. The solver can
be indicate in the following way 'solver=gurobi'
"""

import click
from osemosys_step import data_split as ds
from osemosys_step import main_utils as mu
from osemosys_step import (
    utils,
    preprocess_data,
    solve
)
import os
from pathlib import Path
import pandas as pd
import shutil
from tqdm import tqdm
import logging
import sys
import glob
import subprocess

from otoole import read, write

logger = logging.getLogger(__name__)

from snakemake.utils import min_version
min_version("8.0")

@click.group()
def cli():
    pass

@click.command()
@click.option("--step_length", required=True, multiple=True,
              help="""
              Provide an integer to indicate the step length, e.g. '5' for
              five year steps. One can provide the parameter also twice, for
              example if the first step shall be one year and all following five
              years one would enter '--step_length 1 --step_length 5'
              """)
@click.option("--input_data", required=True, default= '../data/utopia.txt',
              help="The path to the input datafile. relative from the src folder, e.g. '../data/utopia.txt'")
@click.option("--solver", default="cbc",
              help="Available solvers are 'glpk', 'cbc', and 'gurobi'. Default is 'cbc'")
@click.option("--cores", default=1, show_default=True,
              help="Number of cores snakemake is allowed to use.")
@click.option("--foresight", default=None,
              help="""Allows the user to indicated the number of years of foresight,
                i.e., beyond the years in a step.
                """)
@click.option("--path_param", default=None,
              help="""If the scenario data for the decisions between the steps is
              saved elsewhere than '../data/scenarios/' on can use this option to
              indicate the path.
              """)
def run(input_data: str, step_length: int, path_param: str, cores: int, solver=None, foresight=None):
    """Main entry point for workflow"""

    ##########################################################################
    # Check for needed software
    ##########################################################################

    # GLPK is needed for the generation of lp file. Hence, it is always needed for running OSeMOSYS_step.
    try:
        cmd = f"glpsol --help"
        subprocess.run(cmd, shell = True)
    except:
        logger.error(f"Can't call GLPK. Make sure GLPK is installed on your computer.")
        print("Can't call GLPK. Make sure GLPK is installed on your computer.")
        sys.exit()

    ##########################################################################
    # Setup directories
    ##########################################################################

    # Note that when running from the command line entry point, these paths will be relative
    # to the local path from which the command is run.
    data_dir = Path("data")
    step_dir = Path("steps")
    results_dir = Path("results")
    model_dir = Path("model")
    logs_dir = Path("logs")

    for f in glob.glob(str(logs_dir / "*.log")):
        os.remove(f)
    logging.basicConfig(filename=str(Path(logs_dir, "log.log")), level=logging.WARNING)

    ##########################################################################
    # Remove previous run data
    ##########################################################################

    for dir in glob.glob(str(data_dir / "data*/")):
        # remove both "data/" and "data_*/" folders
        shutil.rmtree(dir)
    utils.check_for_directory(Path(data_dir, "data"))

    for dir in glob.glob(str(data_dir / "step_*/")):
        shutil.rmtree(dir)

    for dir in glob.glob(str(results_dir / "*/")):
        shutil.rmtree(dir)

    for dir in glob.glob(str(step_dir / "*/")):
        shutil.rmtree(dir)

    if Path(logs_dir, "solves").exists():
        shutil.rmtree(str(Path(logs_dir, "solves")))

    ##########################################################################
    # Setup data and folder structure
    ##########################################################################

    # Create scenarios folder
    if path_param:
        scenario_dir = Path(path_param)
    else:
        scenario_dir = Path(data_dir, "scenarios")

    # format step length
    step_length = utils.format_step_input(step_length)

    # Create folder of csvs from datafile
    otoole_csv_dir = Path(data_dir, "data")
    otoole_config_path = Path(data_dir, "otoole_config.yaml")
    utils.datafile_to_csv(str(input_data), str(otoole_csv_dir), otoole_config_path)

    # get step length parameters
    otoole_data, otoole_defaults = read(otoole_config_path, "csv", str(otoole_csv_dir))
    if not foresight==None:
        actual_years_per_step, modelled_years_per_step, num_steps = ds.split_data(otoole_data, step_length, foresight=foresight)
    else:
        actual_years_per_step, modelled_years_per_step, num_steps = ds.split_data(otoole_data, step_length)

    # write out original parsed step data
    for step, years_per_step in modelled_years_per_step.items():
        step_data = ds.get_step_data(otoole_data, years_per_step)
        write(otoole_config_path, "csv", str(Path(data_dir, f"data_{step}")), step_data, otoole_defaults)
        logger.info(f"Wrote data for step {step}")

    # dictionary for steps with new scenarios
    steps = mu.get_step_data(str(scenario_dir)) # returns Dict[int, Dict[str, pd.DataFrame]]

    # get option combinations per step
    step_options = mu.get_options_per_step(steps) # returns Dict[int, List[str]]
    step_options = mu.add_missing_steps(step_options, num_steps)
    step_options = mu.append_step_num_to_option(step_options)

    # create option directores in data/
    mu.create_option_directories(str(data_dir), step_options, step_directories=True)

    # create option directories in steps/
    if not step_dir.exists():
        step_dir.mkdir()
    mu.create_option_directories(str(step_dir), step_options, step_directories=True)

    # create option directories in results/
    if not results_dir.exists():
        results_dir.mkdir()
    mu.create_option_directories(str(results_dir), step_options, step_directories=False)
    if not utils.check_for_subdirectory(results_dir):
        all_res_dir = Path(results_dir, 'the_scen')
        all_res_dir.mkdir(exist_ok=True)

    # copy over step/scenario/option data
    mu.copy_reference_option_data(src_dir=data_dir, dst_dir=data_dir, options_per_step=step_options)

    ##########################################################################
    # Apply options to input data
    ##########################################################################

    step_option_data = mu.get_option_data_per_step(steps) # {int, Dict[str, pd.DataFrame]}
    option_data_by_param = mu.get_param_data_per_option(step_option_data) # Dict[str, Dict[str, pd.DataFrame]]

    for step_num in range(0, num_steps + 1):

        step_dir_number = Path(data_dir, f"step_{step_num}")

        # get grouped list of options to apply - ie. [A0-B1, C0]

        for option_dir in utils.get_subdirectories(str(step_dir_number)):
            grouped_options_to_apply = Path(option_dir).parts
            parsed_options_to_apply = []

            # get parsed list of options to apply - ie. [A0, B1, C0]

            for grouped_option_to_apply in grouped_options_to_apply:
                if grouped_option_to_apply in ["..", "data", f"step_{step_num}"]:
                    continue
                parsed_options = grouped_option_to_apply.split("-")
                for parsed_option_to_apply in parsed_options:
                    parsed_options_to_apply.append(parsed_option_to_apply)

            #  at this point, parsed_options_to_apply = [A0, B1, C0]

            for option_to_apply in parsed_options_to_apply:
                for param, param_data in option_data_by_param[option_to_apply].items():
                    path_to_data = Path(option_dir, f"{param}.csv")
                    original = pd.read_csv(path_to_data)
                    param_data_year_filtered = param_data.loc[param_data["YEAR"].isin(modelled_years_per_step[step_num])].reset_index(drop=True)
                    new = mu.apply_option_data(original, param_data_year_filtered)
                    new.to_csv(path_to_data, index=False)

    ##########################################################################
    # Loop over steps
    ##########################################################################

    csv_dirs = mu.get_option_combinations_per_step(step_options)

    for step, options in tqdm(csv_dirs.items(), total=len(csv_dirs), desc="Building and Solving Models", bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):

        ######################################################################
        # Create Datafile
        ######################################################################

        if not options:
            csvs = Path(data_dir, f"step_{step}")
            data_file = Path(step_dir, f"step_{step}", "data.txt")
            data_file_pp = Path(step_dir, f"step_{step}", "data_pp.txt")
            mu.create_datafile(csvs, data_file, otoole_config_path)
            preprocess_data.main("otoole", str(data_file), str(data_file_pp))
        else:
            for option in options:
                csvs = Path(data_dir, f"step_{step}")
                data_file = Path(step_dir, f"step_{step}")
                for each_option in option:
                    csvs = csvs.joinpath(each_option)
                    data_file = data_file.joinpath(each_option)
                if not data_file.exists():
                    logger.warning(f"{str(data_file)} not created")
                    # failed = True
                else:
                    data_file_pp = data_file.joinpath("data_pp.txt") # preprocessed
                    data_file = data_file.joinpath("data.txt") # need non-preprocessed for otoole results
                    mu.create_datafile(csvs, data_file, otoole_config_path)
                    preprocess_data.main("otoole", str(data_file), str(data_file_pp))

        ######################################################################
        # Create LP file
        ######################################################################

        osemosys_file = Path(model_dir, "osemosys.txt")
        failed_lps = []

        if not options:
            lp_file = Path(step_dir, f"step_{step}", "model.lp")
            datafile = Path(step_dir, f"step_{step}", "data_pp.txt")
            lp_log_dir = Path("logs", "solves", f"step_{step}")
            lp_log_dir.mkdir(parents=True, exist_ok=True)
            lp_log_file = Path(lp_log_dir,"lp.log")

            exit_code = solve.create_lp(str(datafile), str(lp_file), str(osemosys_file), str(lp_log_file))
            if exit_code == 1:
                logger.error(f"{str(lp_file)} could not be created")
                failed_lps.append(lp_file)
        else:
            for option in options:
                lp_file = Path(step_dir, f"step_{step}")
                datafile = Path(step_dir, f"step_{step}")
                lp_log_dir = Path("logs", "solves", f"step_{step}")
                lp_log_file = Path(lp_log_dir,"lp.log")
                for each_option in option:
                    lp_file = lp_file.joinpath(each_option)
                    datafile = datafile.joinpath(each_option)
                    lp_log_dir = lp_log_dir.joinpath(each_option)
                lp_file = lp_file.joinpath("model.lp")
                datafile = datafile.joinpath("data_pp.txt")
                lp_log_dir.mkdir(parents=True, exist_ok=True)
                lp_log_file = Path(lp_log_dir,"lp.log")
                exit_code = solve.create_lp(str(datafile), str(lp_file), str(osemosys_file), str(lp_log_file))
                if exit_code == 1:
                    logger.error(f"{str(lp_file)} could not be created")
                    failed_lps.append(lp_file)

        ######################################################################
        # Remove failed builds
        ######################################################################

        for failed_lp in failed_lps:

            # remove the step folder
            directory_path = Path(failed_lp).parent
            if directory_path.exists():
                shutil.rmtree(str(directory_path))

            # remove the corresponding folder in results/
            result_options = []
            while directory_path.name != f"step_{step}":
                result_options.insert(0, directory_path.name)
                directory_path = directory_path.parent
            result_option_path = Path(results_dir).joinpath(*result_options)
            if result_option_path == results_dir:
                logger.error("Top level run failed :(")
                for item in result_option_path.glob('*'):
                    if not item.name == ".gitkeep":
                        shutil.rmtree(item)
                sys.exit()
            elif result_option_path.exists():
                shutil.rmtree(str(result_option_path))

        ######################################################################
        # Solve the model
        ######################################################################

        # get lps to solve

        lps_to_solve = []

        if not options:
            lp_file = Path("..", "..", step_dir, f"step_{step}", "model.lp")
            sol_dir = Path(step_dir, f"step_{step}")
            lps_to_solve.append(str(lp_file))
        else:
            for option in options:
                lp_file = Path(step_dir, f"step_{step}")
                sol_dir = Path(step_dir, f"step_{step}")
                for each_option in option:
                    lp_file = lp_file.joinpath(each_option)
                lp_file = lp_file.joinpath("model.lp")
                if lp_file.exists():
                    lp_file = Path("..", "..", lp_file)
                    lps_to_solve.append(str(lp_file))

        # run snakemake

        #######
        # I think the multiprocessing library may be a better option then this
        # since snakemake is a little overkill for running a single function
        # when the goal is to just parallize multiple function calls
        #######

        # pretty sure there is a way to directly use the SnakemakeApi class! 
        snakefile_args = [
            "--snakefile src/osemosys_step/snakefile", 
            f"--config solver={solver} files={[','.join(lps_to_solve)]}",
            f"--cores {cores}",
            "--keep-going",
            "--quiet"
        ]
        subprocess.run(f"snakemake {' '.join(snakefile_args)}", shell = True)
        
        ######################################################################
        # Check for solutions
        ######################################################################

        failed_sols = []

        if not options:
            sol_file = Path(step_dir, f"step_{step}", "model.sol")
            if not sol_file.exists():
                failed_sols.append(str(sol_file))
            elif solver == "cbc":
                if solve.check_cbc_feasibility(str(sol_file)) == 1:
                    failed_sols.append(str(sol_file))
            elif solver == "glpk":
                if solve.check_glpk_feasibility(str(sol_file)) == 1:
                    failed_sols.append(str(sol_file))
            elif solver == "gurobi":
                if solve.check_gurobi_feasibility(str(sol_file)) == 1:
                    failed_sols.append(str(sol_file))
            elif solver == "cplex":
                print("CPLEX solution not checked")

        else:
            for option in options:
                sol_file = Path(step_dir, f"step_{step}")
                for each_option in option:
                    sol_file = sol_file.joinpath(each_option)
                sol_file = sol_file.joinpath("model.sol")
                if not sol_file.exists():
                    failed_sols.append(str(sol_file))
                elif solver == "cbc":
                    if solve.check_cbc_feasibility(str(sol_file)) == 1:
                        failed_sols.append(str(sol_file))
                elif solver == "glpk":
                    if solve.check_glpk_feasibility(str(sol_file)) == 1:
                        failed_sols.append(str(sol_file))
                elif solver == "gurobi":
                    if solve.check_gurobi_feasibility(str(sol_file)) == 1:
                        failed_sols.append(str(sol_file))
                elif solver == "cplex":
                    print("CPLEX solution not checked")

        ######################################################################
        # Remove failed solves
        ######################################################################

        if failed_sols:
            for failed_sol in failed_sols:

                logger.warning(f"Model {failed_sol} failed solving")

                # get failed options
                failed_options = utils.get_options_from_path(failed_sol, ".sol") # returns ["1E0-1C0", "2C1"]

                # remove options from results
                result_option_path = Path(results_dir).joinpath(*failed_options)
                if result_option_path == results_dir:
                    logger.error("All runs failed, quitting...")
                    sys.exit()
                elif result_option_path.exists():
                    shutil.rmtree(str(result_option_path))

                # remove options from current and future steps
                step_to_delete = step
                while step_to_delete <= num_steps:
                    step_option_path = Path(step_dir, f"step_{step_to_delete}").joinpath(*failed_options)
                    if step_option_path.exists():
                        shutil.rmtree(str(step_option_path))
                    step_to_delete += 1

        ######################################################################
        # Generate result CSVs
        ######################################################################
        if not solver == "glpk": #csvs already created
            if not options:
                sol_dir = Path(step_dir, f"step_{step}")
                if sol_dir.exists():
                    sol_file = Path(sol_dir, "model.sol")
                    data_file = Path(sol_dir, "data.txt")
                    solve.generate_results(
                        sol_file=str(sol_file),
                        solver=solver,
                        config=otoole_config_path,
                        data_file=str(data_file)
                    )
            else:
                for option in options:
                    sol_dir = Path(step_dir, f"step_{step}")
                    for each_option in option:
                        sol_dir = sol_dir.joinpath(each_option)
                    if sol_dir.exists():
                        sol_file = Path(sol_dir, "model.sol")
                        data_file = Path(sol_dir, "data.txt")
                        solve.generate_results(
                            sol_file=str(sol_file),
                            solver=solver,
                            config=otoole_config_path,
                            data_file=str(data_file)
                        )

        ######################################################################
        # Save Results
        ######################################################################

        if not options:
            # apply data to all options
            sol_results_dir = Path(step_dir, f"step_{step}", "results")
            if not sol_results_dir.exists():
                logger.error("All runs failed")
                sys.exit()
            for subdir in utils.get_subdirectories(str(results_dir)):
                for result_file in sol_results_dir.glob("*"):
                    src = result_file
                    dst = Path(subdir, result_file.name)
                    src_df = pd.read_csv(str(src))
                    if not dst.exists():
                        if "YEAR" in src_df.columns:
                            result_df = src_df.loc[src_df["YEAR"].isin(actual_years_per_step[step])].reset_index(drop=True)
                        else:
                            result_df = src_df
                    else:
                        dst_df = pd.read_csv(str(dst))
                        result_df = utils.concat_dataframes(src=src_df, dst=dst_df, years=actual_years_per_step[step])
                    result_df.to_csv(str(dst), index=False)

        else:
            for option in options:

                # get top level result paths
                sol_results_dir = Path(step_dir, f"step_{step}")
                dst_results_dir = results_dir

                # apply max option level for the step
                for each_option in option:
                    sol_results_dir = sol_results_dir.joinpath(each_option)
                    dst_results_dir = dst_results_dir.joinpath(each_option)

                if not dst_results_dir.exists(): # failed solve
                    continue

                # find if there are more nested options for each step
                dst_result_subdirs = utils.get_subdirectories(str(dst_results_dir))
                if not dst_result_subdirs:
                    dst_result_subdirs = [dst_results_dir]

                # copy results
                sol_results_dir = Path(sol_results_dir, "results")
                for result_file in sol_results_dir.glob("*"):
                    for dst_results_dir in dst_result_subdirs:
                        src = result_file
                        dst = Path(dst_results_dir, result_file.name)
                        if not dst.exists():
                            shutil.copy(str(src), str(dst))
                        else:
                            src_df = pd.read_csv(str(src))
                            dst_df = pd.read_csv(str(dst))
                            result_df = utils.concat_dataframes(src=src_df, dst=dst_df, years=actual_years_per_step[step])
                            result_df.to_csv(str(dst), index=False)

        ######################################################################
        # Update data for next step
        ######################################################################

        # skip on last step
        if step + 1 > num_steps:
            continue

        step_dir_data = Path(data_dir, f"step_{step}")

        options_next_step = csv_dirs[step + 1]

        # no options in current step or next step
        if not options_next_step:
            logger.info(f"Step {step} does not have options, and step {step + 1} does not have options")

            # Get updated residual capacity values
            step_dir_results = Path(step_dir, f"step_{step}", "results")

            old_res_cap = mu.get_res_cap_next_steps(step, num_steps, data_dir, actual_years_per_step)

            op_life = pd.read_csv(str(Path(step_dir_data, "OperationalLife.csv")))
            new_cap = pd.read_csv(str(Path(step_dir_results, "NewCapacity.csv")))

            res_cap = mu.update_res_capacity(
                res_capacity=old_res_cap,
                op_life=op_life,
                new_capacity=new_cap,
                step_years=actual_years_per_step[step]
            )

            # overwrite residual capacity values for all subsequent steps
            next_step = step + 1
            while next_step < num_steps + 1:

                step_res_cap = res_cap.loc[res_cap["YEAR"].isin(modelled_years_per_step[next_step])]

                # no more res capacity to pass on
                if step_res_cap.empty:
                    break

                step_dir_to_update = Path(data_dir, f"step_{next_step}")

                if not utils.check_for_subdirectory(str(step_dir_to_update)):
                    step_res_cap.to_csv(str(Path(step_dir_to_update, "ResidualCapacity.csv")), index=False)

                else:
                    for subdir in utils.get_subdirectories(str(step_dir_to_update)):
                        step_res_cap.to_csv(str(Path(subdir, "ResidualCapacity.csv")), index=False)

                next_step += 1

        # no options in current step, but options in next step
        elif (not options) and (options_next_step):
            logger.info(f"Step {step} does not have options, and step {step + 1} does have options")

            option_dir_data = Path(data_dir, f"step_{step}")
            option_dir_results = Path(step_dir, f"step_{step}", "results")

            if not option_dir_results.exists(): # failed solve
                continue

            # Get updated residual capacity values
            op_life = pd.read_csv(str(Path(option_dir_data, "OperationalLife.csv")))
            new_cap = pd.read_csv(str(Path(option_dir_results, "NewCapacity.csv")))

            # overwrite residual capacity values for all subsequent steps
            next_step = step + 1
            while next_step < num_steps + 1:

                # apply to max option level for the step
                option_dir_to_update = Path(data_dir, f"step_{next_step}")

                for subdir in utils.get_subdirectories(str(option_dir_to_update)):
                    old_res_cap = pd.read_csv(str(Path(subdir, "ResidualCapacity.csv")))
                    res_cap = mu.update_res_capacity(
                        res_capacity=old_res_cap,
                        op_life=op_life,
                        new_capacity=new_cap,
                        step_years=actual_years_per_step[step]
                    )
                    res_cap = res_cap.loc[res_cap["YEAR"].isin(modelled_years_per_step[next_step])]
                    res_cap.to_csv(str(Path(subdir, "ResidualCapacity.csv")), index=False)

                next_step += 1

        # options in current step and next step
        else:
            logger.info(f"Step {step} has options, and step {step + 1} has options")

            for option in options:

                option_dir_data = Path(data_dir, f"step_{step}")
                option_dir_results = Path(step_dir, f"step_{step}")

                # apply max option level for the step
                for each_option in option:
                    option_dir_data = option_dir_data.joinpath(each_option)
                    option_dir_results = option_dir_results.joinpath(each_option)
                option_dir_results = option_dir_results.joinpath("results")
                if not option_dir_results.exists(): # failed solve
                    continue

                # Get updated residual capacity values

                op_life = pd.read_csv(str(Path(option_dir_data, "OperationalLife.csv")))
                new_cap = pd.read_csv(str(Path(option_dir_results, "NewCapacity.csv")))

                # overwrite residual capacity values for all subsequent steps
                next_step = step + 1
                while next_step < num_steps + 1:

                    # apply to max option level for the step
                    option_dir_to_update = Path(data_dir, f"step_{next_step}")
                    for each_option in option:
                        option_dir_to_update = option_dir_to_update.joinpath(each_option)

                    if utils.check_for_subdirectory(str(option_dir_to_update)):
                        for subdir in utils.get_subdirectories(str(option_dir_to_update)):
                            old_res_cap = pd.read_csv(str(Path(subdir, "ResidualCapacity.csv")))
                            res_cap = mu.update_res_capacity(
                                res_capacity=old_res_cap,
                                op_life=op_life,
                                new_capacity=new_cap,
                                step_years=actual_years_per_step[step]
                            )
                            res_cap = res_cap.loc[res_cap["YEAR"].isin(modelled_years_per_step[next_step])]
                            res_cap.to_csv(str(Path(subdir, "ResidualCapacity.csv")), index=False)
                    else:
                        old_res_cap = pd.read_csv(str(Path(option_dir_to_update, "ResidualCapacity.csv")))
                        res_cap = mu.update_res_capacity(
                            res_capacity=old_res_cap,
                            op_life=op_life,
                            new_capacity=new_cap,
                            step_years=actual_years_per_step[step]
                        )
                        res_cap = res_cap.loc[res_cap["YEAR"].isin(modelled_years_per_step[next_step])]
                        res_cap.to_csv(str(Path(option_dir_to_update, "ResidualCapacity.csv")), index=False)

                    next_step += 1

@click.command()
@click.option("--path", required=True, default= '.',
    help="Path where the directory structure shall be created."
)
def setup(path: str):
    """Function to create directory structure in which OSeMOSYS_step can be run.
    The created directory has the below structure:
    ```bash
    OSeMOSYS_step
    ├── data
    │   ├── scenarios
    ├── model
    ├── results
    └── steps
    ```
    """

    dirs = ['data', ['data', 'scenarios'], 'logs', 'model', 'results', 'steps']

    for d in dirs:
        if type(d) == list:
            p = Path(path, *d)
        else:
            p = Path(path, d)
        if not p.exists():
            p.mkdir()

cli.add_command(run)
cli.add_command(setup)

if __name__ == '__main__':
    cli()
