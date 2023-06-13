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
from tqdm import trange, tqdm
import subprocess
import yaml
import logging
import sys


path_log = os.path.join("..", "logs", "log.log")
logging.basicConfig(filename=path_log, level=logging.WARNING)
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

    # set up solver logs
    path_sol_logs = os.sep.join(["..", "logs", "solv_logs"])
    try: 
        os.mkdir(path_sol_logs)
    except FileExistsError:
        pass
    
    ##########################################################################
    # Remove previous run data
    ##########################################################################
    
    subprocess.run(["cd ..", "bash clean.sh"], shell = True)
    
    ##########################################################################
    # Setup data and folder structure 
    ##########################################################################
    
    # Create scenarios folder
    if path_param == None:
        dir_name = os.getcwd()
        path_param = os.path.join(os.sep.join(dir_name.split(os.sep)[:-1]),'data','scenarios')
        
    # format step length 
    step_length = utils.format_step_input(step_length)

    # get step length parameters 
    years_per_step, _ = ds.split_data(input_data, step_length)
    num_steps = len(years_per_step)
    
    # dictionary for steps with new scenarios
    steps = mu.get_step_data(path_param) # returns Dict[int, Dict[str, pd.DataFrame]]
    
    # get option combinations per step
    step_options = mu.get_options_per_step(steps) # returns Dict[int, List[str]]
    step_options = mu.add_missing_steps(step_options, num_steps)
    step_options = mu.append_step_num_to_option(step_options) 
    
    # create option directores in data/
    data_dir = Path("..", "data")
    mu.create_option_directories(str(data_dir), step_options, step_directories=True)
    
    # create option directories in steps/
    step_dir = Path("..", "steps")
    if not step_dir.exists():
        step_dir.mkdir()
    mu.create_option_directories(str(step_dir), step_options, step_directories=True)
    
    # create option directories in results/
    results_dir = Path("..", "results")
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

    for step_num in range(0, num_steps):
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
                    param_data_year_filtered = param_data.loc[param_data["YEAR"].isin(years_per_step[step_num])].reset_index(drop=True)
                    new = mu.apply_option_data(original, param_data_year_filtered)
                    new.to_csv(path_to_data, index=False)
 
    ##########################################################################
    # Loop over steps
    ##########################################################################
 
    csv_dirs = mu.get_option_combinations_per_step(step_options)
    otoole_config = utils.read_otoole_config(Path("..", "data", "otoole_config.yaml"))
    
    for step, options in tqdm(csv_dirs.items(), total=len(csv_dirs), desc="Building and Solving Models", bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
        
        ######################################################################
        # Create Datafile
        ######################################################################

        if not options:
            csvs = Path("..", "data", f"step_{step}")
            datafile = Path("..", "steps", f"step_{step}", "data.txt")
            mu.create_datafile(csvs, datafile, otoole_config)
            preprocess_data.main("otoole", datafile, datafile)
        else:
            for option in options:
                csvs = Path("..", "data", f"step_{step}")
                datafile = Path("..", "steps", f"step_{step}")
                for each_option in option:
                    csvs = csvs.joinpath(each_option)
                    datafile = datafile.joinpath(each_option)
                datafile = datafile.joinpath("data.txt")
                mu.create_datafile(csvs, datafile, otoole_config)
                preprocess_data.main("otoole", datafile, datafile)

        ######################################################################
        # Create LP file 
        ######################################################################

        osemosys_file = Path("..", "model", "osemosys.txt")
        failed_lps = []

        if not options:
            lp_file = Path("..", "steps", f"step_{step}", "model.lp")
            datafile = Path("..", "steps", f"step_{step}", "data.txt")
            exit_code = solve.create_lp(str(datafile), str(lp_file), str(osemosys_file))
            if exit_code == 1:
                failed_lps.append(lp_file)
        else:
            for option in options:
                lp_file = Path("..", "steps", f"step_{step}")
                datafile = Path("..", "steps", f"step_{step}") 
                for each_option in option:
                    lp_file = lp_file.joinpath(each_option)
                    datafile = datafile.joinpath(each_option)
                lp_file = lp_file.joinpath("model.lp")
                datafile = datafile.joinpath("data.txt")
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
            if result_option_path == Path("..", "results"):
                logger.error("Top level run failed :(")
                for item in result_option_path.glob('*'):
                    shutil.rmtree(item)
            elif os.path.exists(str(result_option_path)):
                shutil.rmtree(str(result_option_path))

        ######################################################################
        # Solve the model 
        ######################################################################
        
        # get lps to solve 
    
        lps_to_solve = []
        
        if not options:
            lp_file = Path("..", "steps", f"step_{step}", "model.lp")
            sol_dir = Path("..", "steps", f"step_{step}")
            lps_to_solve.append(str(lp_file))
        else:
            for option in options:
                lp_file = Path("..", "steps", f"step_{step}")
                sol_dir = Path("..", "steps", f"step_{step}")
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
        # Remove failed solves 
        ######################################################################

        failed_sols = []

        # check for solution 
        
        if not options:
            sol_file = Path("..", "steps", f"step_{step}", "model.sol")
            if not sol_file.exists():
                failed_sols.append(str(sol_file))
        else:
            for option in options:
                sol_file = Path("..", "steps", f"step_{step}")
                for each_option in option:
                    sol_file = sol_file.joinpath(each_option)
                sol_file = sol_file.joinpath("model.sol")
                if not sol_file.exists():
                    failed_sols.append(str(sol_file))
        
        # remove folder if no .sol file exists
        
        for failed_sol in failed_sols:
            directory_path = Path(failed_sol).parent
            if os.path.exists(str(directory_path)):
                shutil.rmtree(str(directory_path))

            # remove the corresponding folder in results/
            result_options = []
            while directory_path.name != f"step_{step}":
                result_options.insert(0, directory_path.name)
                directory_path = directory_path.parent
            result_option_path = Path(results_dir).joinpath(*result_options)
            if result_option_path == Path("..", "results"):
                logger.error("All runs failed")
                sys.exit("Quitting... ")
            elif os.path.exists(str(result_option_path)):
                shutil.rmtree(str(result_option_path))

        ######################################################################
        # Generate result CSVs
        ######################################################################
 
        if not options:
            sol_dir = Path("..", "steps", f"step_{step}")
            if sol_dir.exists():
                sol_file = Path(sol_dir, "model.sol")
                solve.generate_results(str(sol_file), solver, otoole_config)
        else:
            for option in options:
                sol_dir = Path("..", "steps", f"step_{step}")
                for each_option in option:
                    sol_dir = sol_dir.joinpath(each_option)
                if sol_dir.exists():
                    sol_file = Path(sol_dir, "model.sol")
                    solve.generate_results(str(sol_file), solver, otoole_config)
 
        ######################################################################
        # Save Results 
        ######################################################################
        
        if not options:
            # apply data to all options
            sol_results_dir = Path("..", "steps", f"step_{step}", "results")
            if not sol_results_dir.exists():
                logger.error("All runs failed")
                sys.exit("Quitting...")
            for subdir in utils.get_subdirectories(str(results_dir)):
                for result_file in sol_results_dir.glob("*"):
                    utils.merge_csvs(src=str(result_file), dst=str(Path(subdir, result_file.name)), years=years_per_step[step])
            
        else:
            for option in options:
                
                # get top level result paths 
                sol_results_dir = Path("..", "steps", f"step_{step}")
                dst_results_dir = results_dir
                
                # apply max option level for the step 
                for each_option in option:
                    sol_results_dir = sol_results_dir.joinpath(each_option)
                    dst_results_dir = dst_results_dir.joinpath(each_option)
                    
                # find if there are more nested options for each step
                dst_result_subdirs = utils.get_subdirectories(str(dst_results_dir))
                if not dst_result_subdirs:
                    dst_result_subdirs = [dst_results_dir]
                
                # copy results 
                sol_results_dir = Path(sol_results_dir, "results")
                for result_file in sol_results_dir.glob("*"):
                    for dst_results_dir in dst_result_subdirs:
                        utils.merge_csvs(src=str(result_file), dst=str(Path(dst_results_dir, result_file.name)))
    
        ######################################################################
        # Update data for next step
        ######################################################################
        
        # step_num = step
        # while step_num < num_steps:
        #     print(step_num)
        
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
                
                step_res_cap = res_cap.loc[res_cap["YEAR"].isin(years_per_step[next_step])]
                
                # no more res capacity to pass on
                if step_res_cap.empty:
                    break
                
                step_dir_to_update = Path(data_dir, f"step_{next_step}")
                
                for subdir in utils.get_subdirectories(str(step_dir_to_update)):
                    step_res_cap.to_csv(str(Path(step_dir_to_update, "ResidualCapacity.csv")))
                    
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
                
                # Get updated residual capacity values 
                old_res_cap = pd.read_csv(str(Path(option_dir_data, "ResidualCapacity.csv")))
                op_life = pd.read_csv(str(Path(option_dir_data, "OperationalLife.csv")))
                new_cap = pd.read_csv(str(Path(option_dir_results, "NewCapacity.csv")))
                new_res_cap = mu.get_new_capacity_lifetime(op_life, new_cap)
                res_cap = mu.merge_res_capacites(old_res_cap, new_res_cap)
                
                # overwrite residual capacity values for all subsequent steps
                next_step = step + 1
                while next_step < num_steps:
                    
                    step_res_cap = res_cap.loc[res_cap["YEAR"].isin(years_per_step[next_step])]
                    
                    # no more res capacity to pass on
                    if step_res_cap.empty:
                        break
                    
                    # apply max option level for the step 
                    option_dir_to_update = Path(data_dir, f"step_{next_step}")
                    for each_option in option:
                        option_dir_to_update = option_dir_to_update.joinpath(each_option)
                    for subdir in utils.get_subdirectories(str(option_dir_to_update)):
                        step_res_cap.to_csv(str(Path(subdir, "ResidualCapacity.csv")), index=False)
                        
                    next_step += 1
        

if __name__ == '__main__':
    main() #input_data,step_length,path_param,solver)
