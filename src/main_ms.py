"This script is the main script for running multi-scenario (ms) multi-stage OSeMOSYS models"
#%% Import required packages
import pandas as pd
import os
import itertools
import data_split as ds
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
#%% Main function to coordinate the script
def main(data_path,step_length,param_path):
    param_path = '../data/scenarios/' #for testing
    data_path = '../data/utopia.txt' #for testing
    step_length = 5 #for testing
    dic_yr_in_steps, full_steps = ds.split_dp(data_path,step_length)
    all_steps = full_steps + 1
    dec_dic = get_scen(param_path) #Create dictionary for stages with decisions creating new scenarios
    dic_scen_paths =dict()
    for s in range(all_steps):
        #s = 1 # for testing
        data_step_path = '../data/step'+str(s)
        dic_scen_paths[s] = list()
        dic_scen_paths[s].append(data_step_path)
        try:
            os.mkdir(data_step_path)
        except OSError:
            print("Creation of the directory %s failed" % data_step_path)
    for s in range(all_steps):
        if s in dec_dic: # s like step
            choices = []
            for d in dec_dic[s]: # d like decision
                d_list = []
                for o in dec_dic[s][d]['OPTION'].unique():
                    d_list.append(d+str(o))
                choices.append(d_list)
            combinations = list(itertools.product(*choices))
            for step in range(all_steps):
                if step>(s-1):
                    step_paths = dic_scen_paths[step]
                    dic_scen_paths[step] = list()
                    for path in range(len(step_paths)):
                        for p in range(len(combinations)): # p like path
                            scenario = str()
                            for c in range(len(combinations[p])):
                                scenario += combinations[p][c]
                            path_scenario = step_paths[path] + '/' + scenario
                            try:
                                os.mkdir(path_scenario)
                            except OSError:
                                print("Creation of the directory %s failed" % path_scenario)
                            dic_scen_paths[step].append(path_scenario)
                        print('Here we have to create some scenarios')
        else:
            print('Run that stage!')
#%% If run as script
if __name__ == '__main__':
    path_param = '../data/scenarios/'
    path_data = '../data/utopia.txt'
    step_length = 5
    main(path_data,step_length,path_param)