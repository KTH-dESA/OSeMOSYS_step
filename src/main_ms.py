"This script is the main script for running multi-scenario (ms) multi-stage OSeMOSYS models"
#%% Import required packages
from os.path import dirname
import pandas as pd
import os
import subprocess as sp
import itertools
import shutil
import main_step as ms
import data_split as ds
import step_to_final as stf
import results_to_next_step as rtns
import new_scen as ns
import solv as sl
import click

#%% Function to derive scenario information from provided folders and files
def get_scen(path):
    stages = next(os.walk(path))[1]
    dic = dict()
    for s in range(len(stages)):
        path_s = os.path.join(path,stages[s])
        dic[int(stages[s])] = dict()
        for root, dirs, files in os.walk(path_s):
            dec = [f for f in files if not f[0] == '.']
        for d in dec:
            dic[int(stages[s])][d.split('.')[0]] = pd.read_csv(os.path.join(path_s,d))
    return dic
#%% Function to create folder for each step and a dictonary with their paths
def step_directories(path,steps):
    dic_step_paths = dict()
    for s in range(steps):
        path_step = os.path.join(path,'step'+str(s))
        dic_step_paths[s] = list()
        dic_step_paths[s].append(path_step)
        try:
            os.mkdir(path_step)
        except OSError:
            print("Creation of the directory %s failed" % path_step)
    return dic_step_paths
#%% Function to create a dictionary of scenarios per step
def scen_dic(dic_dec,all_steps):
    dic_scen = dict()
    for s in range(all_steps):
        if s in dic_dec: # s like step
            choices = []
            for d in dic_dec[s]: # d like decision
                d_list = []
                for o in dic_dec[s][d]['OPTION'].unique():
                    d_list.append(d+str(o))
                choices.append(d_list)
            combinations = list(itertools.product(*choices))
            dic_scen[s] = dict()
            for p in range(len(combinations)): # p like path
                scenario = str()
                dic_cho = dict()
                for c in range(len(combinations[p])):
                    scenario += combinations[p][c]
                    dic_cho[combinations[p][c][0]] = combinations[p][c][1:]
                dic_scen[s][scenario] = dic_cho
    return dic_scen
#%% Function to create directories for each scenario in each step and a dictionary with the paths
def scen_directories(dic_steps,dic_scen):
    dic_scen_paths = dic_steps
    for s in dic_steps:
        if s in dic_scen:
            for step in dic_steps:
                if step>(s-1):
                    step_paths = dic_scen_paths[step]
                    dic_scen_paths[step] = list()
                    for path in range(len(step_paths)):
                        for p in list(dic_scen[s].keys()):
                            path_scenario = os.path.join(step_paths[path],p)
                            try:
                                os.mkdir(path_scenario)
                            except OSError:
                                print("Creation of the directory %s failed" % path_scenario)
                            dic_scen_paths[step].append(path_scenario)
    return dic_scen_paths
#%% Function to copy datapackages of remaining steps
def copy_dps(step,scen,scen_paths):
    paths_dp = []
    for s in range(len(scen_paths)):
        if step==0:
            for i in range(len(scen_paths[0])):
                src = os.path.join('..','data','datapackage'+str(s))
                dest = os.path.join(scen_paths[step][i], 'datapackage'+str(s))
                destination = shutil.copytree(src,dest)
                paths_dp.append(destination)
        else:
            if step in scen:
                if s>=step:
                    q = 0
                    for i in range(len(scen_paths[step-1])):
                        if scen_paths[step][q]!='none':
                            for j in scen[step]:
                                src = os.path.join(scen_paths[step-1][i], 'datapackage' + str(s))
                                dest = os.path.join(scen_paths[step][q],'datapackage'+str(s))
                                destination = shutil.copytree(src,dest)
                                paths_dp.append(destination)
                                q += 1
                        else:
                            paths_dp.append('none')
            else:
                if s>=step:
                    for i in range(len(scen_paths[step-1])):
                        if scen_paths[step][i]!='none':
                            src = os.path.join(scen_paths[step-1][i], 'datapackage'+str(s))
                            dest = os.path.join(scen_paths[step][i],'datapackage'+str(s))
                            destination = shutil.copytree(src,dest)
                            paths_dp.append(destination)
                        else:
                            paths_dp.append('none')
    return paths_dp
#%% Create directories and paths for final results
def final_paths(scen,paths_p_step,step):
    paths = []
    if step==0:
        if 0 in scen:
            for i in scen[0]:
                paths.append(os.path.join('..','results',i))
        else:
            paths.append(os.path.join('..','results'))
    else:
        if step in scen:
            for j in paths_p_step:
                for i in scen[step]:
                    paths.append(os.path.join(j,i))
        else:
            for j in paths_p_step:
                paths.append(j)
    for p in paths:
        try:
            os.mkdir(p)
        except OSError:
            print("Creation of the directory %s failed" %p)
    return paths
#%% 
def copy_fr(step,dic_scen,paths_res_fin_p):
    """Function to copy final results to scenario folders of next step.
    """
    if step in dic_scen:
        for s in paths_res_fin_p:
            src = os.path.join(s,'res')
            for t in dic_scen[step]:
                dest = os.path.join(s,t,'res')
                shutil.copytree(src,dest)
#%% Main function to coordinate the script
"The main function of main_ms takes always three inputs and can take the optional input solver. The three needed inputs are the path to the datafile of the model, the step length - either an integer in case the step length is always the same or a list of two integers, the first indicating the length of the first step and the second of the remaining steps - and the path to the folder with the csv files containing the data for the parameter to varied between scenarios. The solver can be indicate in the following way 'solver=gurobi'"
# inteact with command prompt or terminal to get all needed input
@click.command()
@click.option("--step_length", required=True, multiple=True, help="Provide an integer to indicate the step length, e.g. '5' for five year steps. One can provide the parameter also twice, for example if the first step shall be one year and all following five years one would enter '--step_length 1 --step_length 5'")
@click.option("--input_data", required=True, default= '../data/utopia.txt', help="The path to the input datafile. relative from the src folder, e.g. '../data/utopia.txt'")
@click.option("--solver", default=None, help="If another solver than 'glpk' is desired please indicate the solver. [gurobi]")
@click.option("--cores", default=1, show_default=True, help="Number of cores snakemake is allowed to use.")
@click.option("--path_param", default=None, help="If the scenario data for the decisions between the steps is safed elsewhere than '../data/scenarios/' on can use this option to indicate the path.")
def main(input_data,step_length,path_param,cores,solver=None):
    log_file = open(os.path.join('..','results','osemosys_step.log'), "w")
    log_file.close()
    if path_param==None:
        """Create path of folder with scenario information."""
        dir_name = os.getcwd()
        path_param = os.path.join(os.sep.join(dir_name.split(os.sep)[:-1]),'data','scenarios')
    if len(step_length)<2:
        """Procedure if the step length is always the same.
        """
        step_length = int(step_length[0])
        dic_yr_in_steps, full_steps = ds.split_dp(input_data,step_length)
        all_steps = len(dic_yr_in_steps)
        dec_dic = get_scen(path_param) #Create dictionary for stages with decisions creating new scenarios
        dic_step_paths = step_directories(os.sep.join(['..','data']),all_steps)
        dic_scen = scen_dic(dec_dic,all_steps)
        dic_scen_paths = scen_directories(dic_step_paths,dic_scen)
        dic_step_res_paths = step_directories(os.sep.join(['..','steps']),all_steps)
        dic_step_scen_paths = scen_directories(dic_step_res_paths,dic_scen)
        dic_fin_res_path = dict()
        for s in range(all_steps):
            paths_dp_step = copy_dps(s,dic_scen,dic_scen_paths)
            paths_in_step = []
            paths_df_in_step = []
            paths_res_in_step = []
            if s==0:
                dic_fin_res_path[s] = final_paths(dic_scen,[],s)
                for sce in range(len(dic_scen_paths[s])):
                    if dic_scen_paths[s][sce] != 'none':
                        if s in dic_scen:
                            ns.main(dic_scen_paths[s][sce],s,dec_dic[s],dic_scen[s][dic_scen_paths[s][sce].split(os.sep)[-1]],dic_yr_in_steps)
                        path_df = os.sep.join(paths_dp_step[sce].split(os.sep)[:-1])+'.txt'
                        paths_df_in_step.append(path_df)
                        ms.dp_to_df(paths_dp_step[sce],path_df)
                        paths_res_in_step.append(dic_step_scen_paths[s][sce])
                        paths_in_step.append(os.sep.join(dic_step_scen_paths[s][sce].split(os.sep)[2:]))

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
                                ns.main(dic_scen_paths[s][i],s,dec_dic[s],dic_scen[s][dic_scen_paths[s][i].split(os.sep)[-1]],dic_yr_in_steps)
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

                print(paths_in_step)
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
        """Procedure if the first step has a different length than the following steps.
        """
        step_length_tp = step_length
        step_length = []
        for l in step_length_tp:
            step_length.append(int(l))
        dic_yr_in_steps, full_steps = ds.split_dp(input_data,step_length)
        all_steps = len(dic_yr_in_steps)
        dec_dic = get_scen(path_param) #Create dictionary for stages with decisions creating new scenarios
        dic_step_paths = step_directories(os.path.join('..','data'),all_steps)
        dic_scen = scen_dic(dec_dic,all_steps)
        dic_scen_paths = scen_directories(dic_step_paths,dic_scen)
        dic_step_res_paths = step_directories(os.path.join('..','steps'),all_steps)
        dic_step_scen_paths = scen_directories(dic_step_res_paths,dic_scen)
        dic_fin_res_path = dict()
        for s in range(all_steps):
            paths_dp_step = copy_dps(s,dic_scen,dic_scen_paths)
            paths_in_step = []
            paths_df_in_step = []
            paths_res_in_step = []
            if s==0:
                dic_fin_res_path[s] = final_paths(dic_scen,[],s)
                for sce in range(len(dic_scen_paths[s])):
                    if dic_scen_paths[s][sce] != 'none':
                        if s in dic_scen:
                            ns.main(dic_scen_paths[s][sce],s,dec_dic[s],dic_scen[s][dic_scen_paths[s][sce].split(os.sep)[-1]],dic_yr_in_steps)
                        path_df = os.sep.join(paths_dp_step[sce].split(os.sep)[:-1])+'.txt'
                        paths_df_in_step.append(path_df)
                        ms.dp_to_df(paths_dp_step[sce],path_df)
                        paths_res_in_step.append(dic_step_scen_paths[s][sce])
                        paths_in_step.append(os.sep.join(dic_step_scen_paths[s][sce].split(os.sep)[2:]))

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
                                ns.main(dic_scen_paths[s][i],s,dec_dic[s],dic_scen[s][dic_scen_paths[s][i].split(os.sep)[-1]],dic_yr_in_steps)
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
#%% If run as script
if __name__ == '__main__':
    main() #input_data,step_length,path_param,solver)