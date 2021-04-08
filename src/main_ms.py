"This script is the main script for running multi-scenario (ms) multi-stage OSeMOSYS models"
#%% Import required packages
import pandas as pd
import os
import itertools
import shutil
import main_step as ms
import data_split as ds
import step_to_final as stf
import results_to_next_step as rtns
#%% Function to derive scenario information from provided folders and files
def get_scen(path):
    #path = '../data/scenarios/' #for testing
    stages = next(os.walk(path))[1]
    dic = dict()
    for s in range(len(stages)):
        path_s = path + stages[s] + '/'
        dic[int(stages[s])] = dict()
        for root, dirs, files in os.walk(path_s):
            dec = [f for f in files if not f[0] == '.']
        for d in dec:
            dic[int(stages[s])][d.split('.')[0]] = pd.read_csv(path_s+d)
    return dic
#%% Function to create folder for each step and a dictonary with their paths
def step_directories(path,steps):
    dic_step_paths = dict()
    for s in range(steps):
        path_step = path + '/step'+str(s)
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
            # step_paths = dic_scen[step]
            dic_scen[s] = list()
            for p in range(len(combinations)): # p like path
                scenario = str()
                for c in range(len(combinations[p])):
                    scenario += combinations[p][c]
                dic_scen[s].append(scenario)
    return dic_scen
#%% Function to create directories for each scenario in each step and a dictionary with the paths
def scen_directories(dic_steps,dic_scen):
    #dic_steps = dic_step_paths #for testing
    #dic_scen = dic_scen #for testing
    dic_scen_paths = dic_steps
    for s in dic_steps:
        if s in dic_scen:
            for step in dic_steps:
                if step>(s-1):
                    step_paths = dic_scen_paths[step]
                    dic_scen_paths[step] = list()
                    for path in range(len(step_paths)):
                        for p in range(len(dic_scen[s])):
                            scenario = dic_scen[s][p]
                            path_scenario = step_paths[path]+'/'+scenario
                            try:
                                os.mkdir(path_scenario)
                            except OSError:
                                print("Creation of the directory %s failed" % path_scenario)
                            dic_scen_paths[step].append(path_scenario)
    return dic_scen_paths
#%% Function to copy datapackages of remaining steps
def copy_dps(step,scen,scen_paths):
    # step = 4 #for testing
    # scen = dic_scen #for testing
    # scen_paths = dic_scen_paths #for testing
    paths_dp = []
    for s in range(len(scen_paths)):
        if step==0:
            for i in range(len(scen_paths[0])):
                src = '../data/datapackage'+str(s)
                dest = scen_paths[step][i]+'/datapackage'+str(s)
                destination = shutil.copytree(src,dest)
                paths_dp.append(destination)
        else:
            if step in scen:
                if s>=step:
                    q = 0
                    for i in range(len(scen_paths[step-1])):
                        for j in scen[step]:
                            src = scen_paths[step-1][i] + '/datapackage' + str(s)
                            dest = scen_paths[step][q]+'/datapackage'+str(s)
                            destination = shutil.copytree(src,dest)
                            paths_dp.append(destination)
                            q += 1
            else:
                if s>=step:
                    for i in range(len(scen_paths[step-1])):
                        src = scen_paths[step-1][i] + '/datapackage' + str(s)
                        dest = scen_paths[step][i]+'/datapackage'+str(s)
                        destination = shutil.copytree(src,dest)
                        paths_dp.append(destination)
    return paths_dp
#%% Create directories and paths for final results
def final_paths(scen,paths_p_step,step):
    paths = []
    if step==0:
        if 0 in scen:
            for i in scen[0]:
                paths.append('../results/'+i+'/')
        else:
            paths.append('../results/')
    else:
        if step in scen:
            for j in paths_p_step:
                for i in scen[step]:
                    paths.append(j+i+'/')
        else:
            for j in paths_p_step:
                paths.append(j)
    for p in paths:
        try:
            os.mkdir(p)
        except OSError:
            print("Creation of the directory %s failed" %p)
    return paths
#%% Function to copy final results to scenario folders of next step
def copy_fr(step,dic_scen,paths_res_fin_p):
    # step = 1 #for testing
    # paths_res_fin_p = dic_fin_res_path[0] #for testing
    if step in dic_scen:
        for s in paths_res_fin_p:
            src = s + 'res'
            for t in dic_scen[step]:
                dest = s + t + '/res'
                shutil.copytree(src,dest)
#%% Main function to coordinate the script
def main(data_path,step_length,param_path):
    # param_path = '../data/scenarios/' #for testing
    # data_path = '../data/utopia.txt' #for testing
    # step_length = [1,5] #for testing
    if type(step_length)==int:
        dic_yr_in_steps, full_steps = ds.split_dp(data_path,step_length)
        all_steps = len(dic_yr_in_steps)
        dec_dic = get_scen(param_path) #Create dictionary for stages with decisions creating new scenarios
        dic_step_paths = step_directories('../data',all_steps)
        dic_scen = scen_dic(dec_dic,all_steps)
        dic_scen_paths = scen_directories(dic_step_paths,dic_scen)
        dic_step_res_paths = step_directories('../steps',all_steps)
        dic_step_scen_paths = scen_directories(dic_step_res_paths,dic_scen)
        dic_fin_res_path = dict()
        for s in range(all_steps):
            paths_dp_step = copy_dps(s,dic_scen,dic_scen_paths)
            if s==0:
                dic_fin_res_path[s] = final_paths(dic_scen,[],s)
                for sce in range(len(dic_scen_paths[s])):
                    path_df = '/'.join(paths_dp_step[sce].split('/')[:-1])+'.txt'
                    ms.dp_to_df(paths_dp_step[sce],path_df)
                    path_res_step = dic_step_scen_paths[s][sce]
                    ms.run_df(path_df,path_res_step)
                    stf.main(path_res_step,dic_fin_res_path[s][sce],s,dic_yr_in_steps[s].iloc[:step_length])
            else:
                dic_fin_res_path[s] = final_paths(dic_scen,dic_fin_res_path[s-1],s)
                copy_fr(s,dic_scen,dic_fin_res_path[s-1])
                i = 0
                for sce in range(len(dic_scen_paths[s-1])):
                    if s in dic_scen:
                        for scn in range(len(dic_scen[s])):
                            path_dp_d = paths_dp_step[i]+'/data'
                            rtns.main(path_dp_d,dic_fin_res_path[s-1][sce])
                            path_df = '/'.join(paths_dp_step[i].split('/')[:-1])+'.txt'
                            ms.dp_to_df(paths_dp_step[i],path_df)
                            path_res_step = dic_step_scen_paths[s][i]
                            ms.run_df(path_df,path_res_step)
                            stf.main(path_res_step,dic_fin_res_path[s][i],s,dic_yr_in_steps[s].iloc[:step_length])
                            i += 1
                    else:
                        path_dp_d = paths_dp_step[sce]+'/data'
                        rtns.main(path_dp_d,dic_fin_res_path[s-1][sce])
                        path_df = '/'.join(paths_dp_step[sce].split('/')[:-1])+'.txt'
                        ms.dp_to_df(paths_dp_step[sce],path_df)
                        path_res_step = dic_step_scen_paths[s][sce]
                        ms.run_df(path_df,path_res_step)
                        stf.main(path_res_step,dic_fin_res_path[s][sce],s,dic_yr_in_steps[s].iloc[:step_length])
    else:
        dic_yr_in_steps, full_steps = ds.split_dp(data_path,step_length)
        all_steps = len(dic_yr_in_steps)
        dec_dic = get_scen(param_path) #Create dictionary for stages with decisions creating new scenarios
        dic_step_paths = step_directories('../data',all_steps)
        dic_scen = scen_dic(dec_dic,all_steps)
        dic_scen_paths = scen_directories(dic_step_paths,dic_scen)
        dic_step_res_paths = step_directories('../steps',all_steps)
        dic_step_scen_paths = scen_directories(dic_step_res_paths,dic_scen)
        dic_fin_res_path = dict()
        for s in range(all_steps):
            paths_dp_step = copy_dps(s,dic_scen,dic_scen_paths)
            if s==0:
                dic_fin_res_path[s] = final_paths(dic_scen,[],s)
                for sce in range(len(dic_scen_paths[s])):
                    path_df = '/'.join(paths_dp_step[sce].split('/')[:-1])+'.txt'
                    ms.dp_to_df(paths_dp_step[sce],path_df)
                    path_res_step = dic_step_scen_paths[s][sce]
                    ms.run_df(path_df,path_res_step)
                    stf.main(path_res_step,dic_fin_res_path[s][sce],s,dic_yr_in_steps[s].iloc[:step_length[0]])
            else:
                dic_fin_res_path[s] = final_paths(dic_scen,dic_fin_res_path[s-1],s)
                copy_fr(s,dic_scen,dic_fin_res_path[s-1])
                i = 0
                for sce in range(len(dic_scen_paths[s-1])):
                    if s in dic_scen:
                        for scn in range(len(dic_scen[s])):
                            path_dp_d = paths_dp_step[i]+'/data'
                            rtns.main(path_dp_d,dic_fin_res_path[s-1][sce])
                            path_df = '/'.join(paths_dp_step[i].split('/')[:-1])+'.txt'
                            ms.dp_to_df(paths_dp_step[i],path_df)
                            path_res_step = dic_step_scen_paths[s][i]
                            ms.run_df(path_df,path_res_step)
                            stf.main(path_res_step,dic_fin_res_path[s][i],s,dic_yr_in_steps[s].iloc[:step_length[1]])
                            i += 1
                    else:
                        path_dp_d = paths_dp_step[sce]+'/data'
                        rtns.main(path_dp_d,dic_fin_res_path[s-1][sce])
                        path_df = '/'.join(paths_dp_step[sce].split('/')[:-1])+'.txt'
                        ms.dp_to_df(paths_dp_step[sce],path_df)
                        path_res_step = dic_step_scen_paths[s][sce]
                        ms.run_df(path_df,path_res_step)
                        stf.main(path_res_step,dic_fin_res_path[s][sce],s,dic_yr_in_steps[s].iloc[:step_length[1]])
#%% If run as script
if __name__ == '__main__':
    path_param = '../data/scenarios/'
    path_data = '../data/utopia.txt'
    step_length = [1,5]
    main(path_data,step_length,path_param)