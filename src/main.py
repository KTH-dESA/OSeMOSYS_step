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
import data_split as ds
import os
from pathlib import Path
import pandas as pd
import shutil
from typing import Dict, List
import utils
import main_utils as mu
import preprocess_data 
import solve
from tqdm import tqdm
import subprocess
import yaml
import logging
import sys
import glob


logger = logging.getLogger(__name__)

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
              help="If another solver than 'glpk' is desired please indicate the solver. [gurobi]")
@click.option("--cores", default=1, show_default=True, 
              help="Number of cores snakemake is allowed to use.")
@click.option("--path_param", default=None, 
              help="""If the scenario data for the decisions between the steps is 
              saved elsewhere than '../data/scenarios/' on can use this option to 
              indicate the path.
              """)
def main(input_data: str, step_length: int, path_param: str, cores: int, solver=None):
    """Main entry point for workflow"""

    ##########################################################################
    # Setup dirctories
    ##########################################################################
    
    data_dir = Path("..", "data")
    step_dir = Path("..", "steps")
    results_dir = Path("..", "results")
    model_dir = Path("..", "model")
    logs_dir = Path("..", "logs")
    
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

    # for f in glob.glob(str(logs_dir / "*.log")):
    #     os.remove(f)
    # Path(logs_dir, "logs.log").touch()

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
    otoole_config = utils.read_otoole_config(str(otoole_config_path))
    utils.datafile_to_csv(str(input_data), str(otoole_csv_dir), otoole_config)

    # get step length parameters 
    otoole_data, otoole_defaults = utils.read_csv(str(otoole_csv_dir), otoole_config)
    actual_years_per_step, modelled_years_per_step, num_steps = ds.split_data(otoole_data, step_length)

    # write out original parsed step data 
    for step, years_per_step in modelled_years_per_step.items():
        step_data = ds.get_step_data(otoole_data, years_per_step)
        utils.write_csv(step_data, otoole_defaults, str(Path(data_dir, f"data_{step}")), otoole_config)
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

        failed = False # for tracking failed builds / solves
        
        ######################################################################
        # Create Datafile
        ######################################################################

        if not options:
            csvs = Path(data_dir, f"step_{step}")
            data_file = Path(step_dir, f"step_{step}", "data.txt")
            data_file_pp = Path(step_dir, f"step_{step}", "data_pp.txt")
            mu.create_datafile(csvs, data_file, otoole_config)
            preprocess_data.main("otoole", str(data_file), str(data_file_pp))
        else:
            for option in options:
                csvs = Path(data_dir, f"step_{step}")
                data_file = Path(step_dir, f"step_{step}")
                for each_option in option:
                    csvs = csvs.joinpath(each_option)
                    data_file = data_file.joinpath(each_option)
                if not data_file.exists(): 
                    failed = True
                else:
                    data_file_pp = data_file.joinpath("data_pp.txt") # preprocessed 
                    data_file = data_file.joinpath("data.txt") # need non-preprocessed for otoole results
                    mu.create_datafile(csvs, data_file, otoole_config)
                    preprocess_data.main("otoole", str(data_file), str(data_file_pp))
        
        if failed:
            continue

        ######################################################################
        # Create LP file 
        ######################################################################

        osemosys_file = Path(model_dir, "osemosys.txt")
        failed_lps = []

        if not options:
            lp_file = Path(step_dir, f"step_{step}", "model.lp")
            datafile = Path(step_dir, f"step_{step}", "data_pp.txt")
            exit_code = solve.create_lp(str(datafile), str(lp_file), str(osemosys_file))
            if exit_code == 1:
                failed_lps.append(lp_file)
        else:
            for option in options:
                lp_file = Path(step_dir, f"step_{step}")
                datafile = Path(step_dir, f"step_{step}") 
                for each_option in option:
                    lp_file = lp_file.joinpath(each_option)
                    datafile = datafile.joinpath(each_option)
                lp_file = lp_file.joinpath("model.lp")
                datafile = datafile.joinpath("data_pp.txt")
                exit_code = solve.create_lp(str(datafile), str(lp_file), str(osemosys_file))
                if exit_code == 1:
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
                print("Top level run failed :(")
                for item in result_option_path.glob('*'):
                    if not item == ".gitignore":
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
            lp_file = Path(step_dir, f"step_{step}", "model.lp")
            sol_dir = Path(step_dir, f"step_{step}")
            lps_to_solve.append(str(lp_file))
        else:
            for option in options:
                lp_file = Path(step_dir, f"step_{step}")
                sol_dir = Path(step_dir, f"step_{step}")
                for each_option in option:
                    lp_file = lp_file.joinpath(each_option)
                lp_file = lp_file.joinpath("model.lp")
                lps_to_solve.append(str(lp_file))
                
        # create a config file for snakemake 
        
        config_path = Path(data_dir, "config.yaml")
        config_data = {"files":lps_to_solve}
        if not solver:
            config_data["solver"] = "cbc"
        else:
            config_data["solver"] = solver
        
        if config_path.exists():
            config_path.unlink()
            
        with open(str(config_path), 'w') as file:
            yaml.dump(config_data, file)

        # run snakemake 
        
        #######
        # I think the multiprocessing library may be a better option then this
        # since snakemake is a little overkill for running a single function
        # when the goal is to just parallize multiple function calls
        #######
        
        cmd = f"snakemake --cores {cores} --keep-going"
        subprocess.run(cmd, shell = True, capture_output = True)
        
        ######################################################################
        # Check for solutions
        ######################################################################

        failed_sols = []
        
        if not options:
            sol_file = Path(step_dir, f"step_{step}", "model.sol")
            if not sol_file.exists():
                failed_sols.append(str(sol_file))
            if solver == "cbc":
                if solve.check_cbc_feasibility(str(sol_file)) == 1:
                    failed_sols.append(str(sol_file))
                    
        else:
            for option in options:
                sol_file = Path(step_dir, f"step_{step}")
                for each_option in option:
                    sol_file = sol_file.joinpath(each_option)
                sol_file = sol_file.joinpath("model.sol")
                if not sol_file.exists():
                    failed_sols.append(str(sol_file))
                if solver == "cbc":
                    if solve.check_cbc_feasibility(str(sol_file)) == 1:
                        failed_sols.append(str(sol_file))

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
                    logger.error("All runs failed")
                    sys.exit("All runs failed :(")
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
 
        if not options:
            sol_dir = Path(step_dir, f"step_{step}")
            if sol_dir.exists():
                sol_file = Path(sol_dir, "model.sol")
                data_file = Path(sol_dir, "data.txt")
                solve.generate_results(
                    sol_file=str(sol_file), 
                    solver=solver, 
                    config=otoole_config, 
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
                        config=otoole_config, 
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
            
        step_dir_number_data = Path(data_dir, f"step_{step}")
        
        if not options:
            
            # Get updated residual capacity values 
            step_dir_number_results = Path(step_dir, f"step_{step}", "results")
            old_res_cap = pd.read_csv(str(Path(step_dir_number_data, "ResidualCapacity.csv")))
            op_life = pd.read_csv(str(Path(step_dir_number_data, "OperationalLife.csv")))
            new_cap = pd.read_csv(str(Path(step_dir_number_results, "NewCapacity.csv")))
            new_res_cap = mu.get_new_capacity_lifetime(op_life, new_cap)
            res_cap = mu.merge_res_capacites(old_res_cap, new_res_cap)
            
            # overwrite residual capacity values for all subsequent steps
            next_step = step + 1
            while next_step < num_steps:

                step_res_cap = res_cap.loc[res_cap["YEAR"].isin(actual_years_per_step[next_step])]
                
                # no more res capacity to pass on
                if step_res_cap.empty:
                    break
                
                step_dir_to_update = Path(data_dir, f"step_{next_step}")
                
                for subdir in utils.get_subdirectories(str(step_dir_to_update)):
                    step_res_cap.to_csv(str(Path(subdir, "ResidualCapacity.csv")), index=False)
                    
                next_step += 1

        else:
            
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
                old_res_cap = pd.read_csv(str(Path(option_dir_data, "ResidualCapacity.csv")))
                op_life = pd.read_csv(str(Path(option_dir_data, "OperationalLife.csv")))
                new_cap = pd.read_csv(str(Path(option_dir_results, "NewCapacity.csv")))
                new_res_cap = mu.get_new_capacity_lifetime(op_life, new_cap)
                res_cap = mu.merge_res_capacites(old_res_cap, new_res_cap)
                
                # overwrite residual capacity values for all subsequent steps
                next_step = step + 1
                while next_step < num_steps:
                    
                    step_res_cap = res_cap.loc[res_cap["YEAR"].isin(actual_years_per_step[next_step])]

                    # no more res capacity to pass on
                    if step_res_cap.empty:
                        break
                    
                    # apply max option level for the step 
                    option_dir_to_update = Path(data_dir, f"step_{next_step}")
                    for each_option in option:
                        option_dir_to_update = option_dir_to_update.joinpath(each_option)
                    subdirs = utils.get_subdirectories(str(option_dir_to_update))
                    if subdirs:
                        for subdir in utils.get_subdirectories(str(option_dir_to_update)):
                            step_res_cap.to_csv(str(Path(subdir, "ResidualCapacity.csv")), index=False)
                    else: # last subdir 
                        step_res_cap.to_csv(str(Path(option_dir_to_update, "ResidualCapacity.csv")), index=False)
                        
                    next_step += 1
        

if __name__ == '__main__':
    main() #input_data,step_length,path_param,solver)
