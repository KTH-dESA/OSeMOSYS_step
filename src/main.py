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

import logging


path_log = os.path.join('..','results','osemosys_step.log')
logging.basicConfig(filename=path_log, level=logging.INFO)
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
@click.option("--solver", default=None, 
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
    path_sol_logs = os.sep.join(['..','results','solv_logs'])
    try: 
        os.mkdir(path_sol_logs)
    except FileExistsError:
        pass
    
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
    
    # create option directores in data/
    data_dir = Path("..", "data")
    mu.create_option_directories(str(data_dir), step_options, step_directories=True)
    
    # create option directories in steps/
    step_dir = Path("..", "steps")
    mu.create_option_directories(str(step_dir), step_options, step_directories=True)
    
    # create option directories in results/
    results_dir = Path("..", "results")
    mu.create_option_directories(str(results_dir), step_options, step_directories=False)
    
    # copy over step/scenario/option data
    mu.copy_reference_option_data(src_dir=data_dir, dst_dir=data_dir, options_per_step=step_options)

    ##########################################################################
    # Apply options to input data
    ##########################################################################
    
    step_option_data = mu.get_option_data_per_step(steps) # {int, Dict[str, pd.DataFrame]}
    option_data_by_param = mu.get_param_data_per_option(step_option_data) # Dict[str, Dict[str, pd.DataFrame]]

    for step_num in trange(0, num_steps, desc="Applying scenario Data", bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
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
    otoole_config = utils.read_otoole_config(Path("..", "data", "config.yaml"))
    
    for step, options in tqdm(csv_dirs.items(), total=len(csv_dirs), desc="Building and Solving Models", bar_format='{l_bar}{bar:10}{r_bar}{bar:-10b}'):
        
        ######################################################################
        # Create Datafile
        ######################################################################

        if not options:
            csvs = Path("..", "data", f"step_{step}")
            datafile = Path("..", "steps", f"step_{step}", "data.txt")
            mu.create_datafile(csvs, datafile, otoole_config)
        else:
            for option in options:
                csvs = Path("..", "data", f"step_{step}")
                datafile = Path("..", "steps", f"step_{step}")
                for each_option in option:
                    csvs = csvs.joinpath(each_option)
                    datafile = datafile.joinpath(each_option)
                datafile = datafile.joinpath("data.txt")
                mu.create_datafile(csvs, datafile, otoole_config)

        ######################################################################
        # Preprocess Datafile
        ######################################################################

        preprocess_data.main("otoole", datafile, datafile)

        ######################################################################
        # Create LP file 
        ######################################################################

        osemosys_file = Path("..", "model", "osemosys.txt")
        failed_lps = []

        if not options:
            lp_file = Path("..", "steps", f"step_{step}", "model.lp")
            exit_code = solve.create_lp(str(datafile), str(lp_file), str(osemosys_file))
            if exit_code == 1:
                failed_lps.append(lp_file)
        else:
            for option in options:
                lp_file = Path("..", "steps", f"step_{step}")
                for each_option in option:
                    lp_file = lp_file.joinpath(each_option)
                lp_file = lp_file.joinpath("model.lp")
                exit_code = solve.create_lp(str(datafile), str(lp_file), str(osemosys_file))
                if exit_code == 1:
                    failed_lps.append(lp_file)

        ######################################################################
        # Remove failed builds 
        ######################################################################

        for failed_lp in failed_lps:
            directory_path = Path(failed_lp).parent
            if os.path.exists(str(directory_path)):
                shutil.rmtree(str(directory_path))

        ######################################################################
        # Solve the model 
        ######################################################################
        
        failed_sols = []
        
        if not options:
            lp_file = Path("..", "steps", f"step_{step}", "model.lp")
            sol_dir = Path("..", "steps", f"step_{step}")
            exit_code = solve.solve(str(lp_file), str(sol_dir), solver)
            if exit_code == 1:
                failed_sols.append(sol_dir)
        else:
            for option in options:
                lp_file = Path("..", "steps", f"step_{step}")
                sol_dir = Path("..", "steps", f"step_{step}")
                for each_option in option:
                    lp_file = lp_file.joinpath(each_option)
                lp_file = lp_file.joinpath("model.lp")
                exit_code = solve.solve(str(lp_file), str(sol_dir), solver)
                if exit_code == 1:
                    failed_sols.append(sol_dir)
        
        ######################################################################
        # Remove failed builds 
        ######################################################################

        for failed_sol in failed_sols:
            directory_path = Path(failed_sol).parent
            if os.path.exists(str(directory_path)):
                shutil.rmtree(str(directory_path))

        ######################################################################
        # Generate result CSVs
        ######################################################################
 
        if not solver:
            pass
        elif not options:
            sol_dir = Path("..", "steps", f"step_{step}")
            if os.path.exists(str(sol_dir)):
                solve.generate_results(str(sol_dir), solver)
        else:
            for option in options:
                sol_dir = Path("..", "steps", f"step_{step}")
                for each_option in option:
                    sol_dir = sol_dir.joinpath(each_option)
                if os.path.exists(str(sol_dir)):
                    solve.generate_results(str(sol_dir), solver)
 
        ######################################################################
        # Results to next step 
        ######################################################################

        # check for last step 
        next_step = step + 1
        if next_step > num_steps:
            continue
        
        elif not options:
            sol_dir = Path("..", "steps", f"step_{step}")
            if os.path.exists(str(sol_dir)):
                mu.results_to_next_step()
                
        else:
            for option in options:
                sol_dir = Path("..", "steps", f"step_{step}")
                for each_option in option:
                    sol_dir = sol_dir.joinpath(each_option)
                if os.path.exists(str(sol_dir)):
                    mu.results_to_next_step()

    ######################################################################
    # Stitch Results together 
    ######################################################################

    

"""

    # Step length is always the same 
    if len(step_length) < 2:
        
        # modify step data based on each option
        option_data = mu.get_option_data_per_step(steps)
        subdirs = [str(p) for p in data_dir.glob("step*/") if p.is_dir()]
        for subdir in subdirs:
            dirs = mu.split_path_name(subdir)
            if len(dirs) == 1:
                continue
            for dir_num, dir_name in enumerate(dirs):
                if dir_num == 0: # skip root dir 
                    continue
                option = option_data[dir_name] # dir_name will be like A0B1 
                for param in option["PARAMETER"].unique():
                    df_name = Path(*subdirs, param, ".csv")
                    df_ref = pd.read_csv(df_name)
                    option_data_to_apply = option.loc[option["PARAMETER"] == param].reset_index(drop=True)
                    df_new = mu.apply_option(df=df_ref, option=option_data_to_apply)
                    df_new.to_csv(df_name)
                    logger.info(f"Applied {param} option data for {dir_name}")
        
        # solve model 
        if solver != None:
            with open('snakefile_tpl.txt', 'r') as file:
                snakefile = file.readlines()
            line_paths = "PATHS = ['" + "',\n'".join(paths_in_step) + "']\n"

            snakefile[1] = line_paths

            with open('snakefile', 'w') as file:
                file.writelines(snakefile)
            
            cd_snakemake = "snakemake --cores %i" % cores
            sp.run([cd_snakemake], shell=True, capture_output=True)

        else:
            i = 0
            for path_df in paths_df_in_step:
                ms.run_df(path_df,paths_res_in_step[i])
                i+=1

                for sce in range(len(dic_scen_paths[s])):
                    if not os.listdir(paths_res_in_step[sce]): #if scenario run failed, this removes following dependent scnearios
                        for z in range(s+1,len(dic_scen_paths)):
                            for x in range(len(dic_scen_paths[z])):
                                if dic_scen_paths[z][x].split(os.sep)[3] == dic_scen_paths[s][sce].split(os.sep)[-1]:
                                    dic_scen_paths[z][x] = 'none'
                    else:
                        stf.main(paths_res_in_step[sce],dic_fin_res_path[s][sce],s,dic_yr_in_steps[s].iloc[:step_length])

            else:
                dic_fin_res_path[s] = final_paths(dic_scen,dic_fin_res_path[s-1],s)
                copy_fr(s,dic_scen,dic_fin_res_path[s-1])
                i = 0
                for sce in range(len(dic_scen_paths[s-1])):
                    if s in dic_scen:
                        for scn in range(len(dic_scen[s])):
                            if dic_scen_paths[s][i] != 'none':
                                path_dp_d = os.path.join(paths_dp_step[i],'data')
                                rtns.main(path_dp_d,dic_fin_res_path[s-1][sce])
                                ns.main(dic_scen_paths[s][i],s,all_scenarios[s],dic_scen[s][dic_scen_paths[s][i].split(os.sep)[-1]],dic_yr_in_steps)
                                path_df = os.sep.join(paths_dp_step[i].split(os.sep)[:-1])+'.txt'
                                paths_df_in_step.append(path_df)
                                ms.dp_to_df(paths_dp_step[i],path_df)
                                paths_res_in_step.append(dic_step_scen_paths[s][i])
                                paths_in_step.append(os.sep.join(dic_step_scen_paths[s][i].split(os.sep)[2:]))

                            i += 1
                        shutil.rmtree(os.path.join(dic_fin_res_path[s-1][sce],'res'))
                    else:
                        if dic_scen_paths[s][sce] != 'none':
                            path_dp_d = os.path.join(paths_dp_step[sce],'data')
                            rtns.main(path_dp_d,dic_fin_res_path[s-1][sce])
                            path_df = os.sep.join(paths_dp_step[sce].split(os.sep)[:-1])+'.txt'
                            paths_df_in_step.append(path_df)
                            ms.dp_to_df(paths_dp_step[sce],path_df)
                            paths_res_in_step.append(dic_step_scen_paths[s][sce])
                            paths_in_step.append(os.sep.join(dic_step_scen_paths[s][sce].split(os.sep)[2:]))

                logger.info("Paths in step %(step)i: %(paths)s" % {'step': s, 'paths': paths_in_step})
                logger.info("Result paths in step %(step)i: %(paths)s" % {'step': s, 'paths': paths_res_in_step})
                if solver != None:
                    with open('snakefile_tpl.txt', 'r') as file:
                        snakefile = file.readlines()
                    line_paths = "PATHS = ['" + "',\n'".join(paths_in_step) + "']\n"

                    snakefile[1] = line_paths

                    with open('snakefile', 'w') as file:
                        file.writelines(snakefile)
                    
                    cd_snakemake = "snakemake --cores %i" % cores
                    sp.run([cd_snakemake], shell=True, capture_output=True)

                else:
                    i = 0
                    for path_df in paths_df_in_step:
                        ms.run_df(path_df,paths_res_in_step[i])
                        i+=1
                for sce in range(len(paths_res_in_step)):
                    if not os.listdir(paths_res_in_step[sce]):
                        p = len(dic_scen_paths[s][sce].split(os.sep))-1
                        for z in range(s+1,len(dic_scen_paths)):
                            for x in range(len(dic_scen_paths[z])):
                                if dic_scen_paths[z][x]!='none':
                                    if dic_scen_paths[z][x].split(os.sep)[p] == dic_scen_paths[s][sce].split(os.sep)[-1]:
                                        dic_scen_paths[z][x] = 'none'
                    else:
                        stf.main(paths_res_in_step[sce],dic_fin_res_path[s][sce],s,dic_yr_in_steps[s].iloc[:step_length])

    else:
        # Procedure if the first step has a different length than the following steps.
        step_length_tp = step_length
        step_length = []
        for l in step_length_tp:
            step_length.append(int(l))
        dic_yr_in_steps, full_steps = ds.split_data(input_data,step_length)
        all_steps = len(dic_yr_in_steps)
        all_scenarios = get_scen(path_param) #Create dictionary for stages with decisions creating new scenarios
        dic_step_paths = step_directories(os.path.join('..','data'),all_steps)
        dic_scen = scen_dic(all_scenarios,all_steps)
        dic_scen_paths = scen_directories(dic_step_paths,dic_scen)
        dic_step_res_paths = step_directories(os.path.join('..','steps'),all_steps)
        dic_step_scen_paths = scen_directories(dic_step_res_paths,dic_scen)
        dic_fin_res_path = dict()
        for s in range(all_steps):
            logger.info('Step %i started' % s)
            paths_dp_step = copy_dps(s,dic_scen,dic_scen_paths)
            paths_in_step = []
            paths_df_in_step = []
            paths_res_in_step = []
            if s==0:
                dic_fin_res_path[s] = final_paths(dic_scen,[],s)
                for sce in range(len(dic_scen_paths[s])):
                    if dic_scen_paths[s][sce] != 'none':
                        if s in dic_scen:
                            ns.main(dic_scen_paths[s][sce],s,all_scenarios[s],dic_scen[s][dic_scen_paths[s][sce].split(os.sep)[-1]],dic_yr_in_steps)
                        path_df = os.sep.join(paths_dp_step[sce].split(os.sep)[:-1])+'.txt'
                        paths_df_in_step.append(path_df)
                        ms.dp_to_df(paths_dp_step[sce],path_df)
                        paths_res_in_step.append(dic_step_scen_paths[s][sce])
                        paths_in_step.append(os.sep.join(dic_step_scen_paths[s][sce].split(os.sep)[2:]))

                logger.info("Paths in step %(step)i: %(paths)s" % {'step': s, 'paths': paths_in_step})
                logger.info("Result paths in step %(step)i: %(paths)s" % {'step': s, 'paths': paths_res_in_step})
                if solver!=None:
                    with open('snakefile_tpl.txt', 'r') as file:
                        snakefile = file.readlines()
                    line_paths = "PATHS = ['" + "',\n'".join(paths_in_step) + "']\n"

                    snakefile[1] = line_paths

                    with open('snakefile', 'w') as file:
                        file.writelines(snakefile)
                    
                    cd_snakemake = "snakemake --cores %i" % cores
                    sp.run([cd_snakemake], shell=True, capture_output=True)

                else:
                    i = 0
                    for path_df in paths_df_in_step:
                        ms.run_df(path_df,paths_res_in_step[i])
                        i+=1

                for sce in range(len(dic_scen_paths[s])):
                    if not os.listdir(paths_res_in_step[sce]): #if scenario run failed, this removes following dependent scnearios
                        for z in range(s+1,len(dic_scen_paths)):
                            for x in range(len(dic_scen_paths[z])):
                                if dic_scen_paths[z][x].split(os.sep)[3] == dic_scen_paths[s][sce].split(os.sep)[-1]:
                                    dic_scen_paths[z][x] = 'none'
                    else:
                        stf.main(paths_res_in_step[sce],dic_fin_res_path[s][sce],s,dic_yr_in_steps[s].iloc[:step_length[0]])

            else:
                dic_fin_res_path[s] = final_paths(dic_scen,dic_fin_res_path[s-1],s)
                copy_fr(s,dic_scen,dic_fin_res_path[s-1])
                i = 0
                for sce in range(len(dic_scen_paths[s-1])):
                    if s in dic_scen:
                        for scn in range(len(dic_scen[s])):
                            if dic_scen_paths[s][i] != 'none':
                                path_dp_d = os.path.join(paths_dp_step[i],'data')
                                rtns.main(path_dp_d,dic_fin_res_path[s-1][sce])
                                ns.main(dic_scen_paths[s][i],s,all_scenarios[s],dic_scen[s][dic_scen_paths[s][i].split(os.sep)[-1]],dic_yr_in_steps)
                                path_df = os.sep.join(paths_dp_step[i].split(os.sep)[:-1])+'.txt'
                                paths_df_in_step.append(path_df)
                                ms.dp_to_df(paths_dp_step[i],path_df)
                                paths_res_in_step.append(dic_step_scen_paths[s][i])
                                paths_in_step.append(os.sep.join(dic_step_scen_paths[s][i].split(os.sep)[2:]))

                            i += 1
                        shutil.rmtree(os.path.join(dic_fin_res_path[s-1][sce],'res'))
                    else:
                        if dic_scen_paths[s][sce] != 'none':
                            path_dp_d = os.path.join(paths_dp_step[sce],'data')
                            rtns.main(path_dp_d,dic_fin_res_path[s-1][sce])
                            path_df = os.sep.join(paths_dp_step[sce].split(os.sep)[:-1])+'.txt'
                            paths_df_in_step.append(path_df)
                            ms.dp_to_df(paths_dp_step[sce],path_df)
                            paths_res_in_step.append(dic_step_scen_paths[s][sce])
                            paths_in_step.append(os.sep.join(dic_step_scen_paths[s][sce].split(os.sep)[2:]))

                logger.info("Paths in step %(step)i: %(paths)s" % {'step': s, 'paths': paths_in_step})
                logger.info("Result paths in step %(step)i: %(paths)s" % {'step': s, 'paths': paths_res_in_step})
                if solver!=None:
                    with open('snakefile_tpl.txt', 'r') as file:
                        snakefile = file.readlines()
                    line_paths = "PATHS = ['" + "',\n'".join(paths_in_step) + "']\n"

                    snakefile[1] = line_paths

                    with open('snakefile', 'w') as file:
                        file.writelines(snakefile)
                    
                    cd_snakemake = "snakemake --cores %i" % cores
                    sp.run([cd_snakemake], shell=True, capture_output=True)

                else:
                    i = 0
                    for path_df in paths_df_in_step:
                        ms.run_df(path_df,paths_res_in_step[i])
                        i += 1
                for sce in range(len(paths_res_in_step)):
                    if not os.listdir(paths_res_in_step[sce]):
                        p = len(dic_scen_paths[s][sce].split(os.sep))-1
                        for z in range(s+1,len(dic_scen_paths)):
                            for x in range(len(dic_scen_paths[z])):
                                if dic_scen_paths[z][x]!='none':
                                    if dic_scen_paths[z][x].split(os.sep)[p] == dic_scen_paths[s][sce].split(os.sep)[-1]:
                                        dic_scen_paths[z][x] = 'none'
                    else:
                        stf.main(paths_res_in_step[sce],dic_fin_res_path[s][sce],s,dic_yr_in_steps[s].iloc[:step_length[1]])


"""

if __name__ == '__main__':
    main() #input_data,step_length,path_param,solver)
