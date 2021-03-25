"This script is the main script for running multi-scenario (ms) multi-stage OSeMOSYS models"
#%% Import required packages
import pandas as pd
import os
import data_split as ds
#%% Function to derive scenario information from provided folders and files
def get_scen(path):
    path = '../data/scenarios/' #for testing
    stages = next(os.walk(path))[1]
    dic = dict()
    for s in range(len(stages)):
        path_s = path + stages[s] + '/'
        for root, dirs, files in os.walk(path_s):
            dic[int(stages[s])] = [f for f in files if not f[0] == '.']
    return dic
#%% Main function to coordinate the script
def main(data_path,step_length,param_path):
    param_path = '../data/scenarios/' #for testing
    data_path = '../data/utopia.txt' #for testing
    step_length = 5 #for testing
    dic_yr_in_steps, full_steps = ds.split_dp(data_path,step_length)
    all_steps = full_steps + 1
    dec_dic = get_scen(param_path) #Create dictionary for stages with decisions creating new scenarios
    for s in range(all_steps):
        if s in dec_dic:
            print('Here we have to create some scenarios')
        else:
            print('Run that stage!')
#%% If run as script
if __name__ == '__main__':
    path_param = '../data/scenarios/'
    path_data = '../data/utopia.txt'
    step_length = 5
    main(path_data,step_length,path_param)