"This script is the main script for running multi-scenario (ms) multi-stage OSeMOSYS models"
#%% Import required packages
import pandas as pd
import os
from .. import data_split
#%% Function to derive scenario information from provided folders and files
def get_scen(path):
    path = '../../data/scenarios/' #for testing
    stages = next(os.walk(path))[1]
    dic = dict() # initialising dictionaries for stages with decisions creating new scenarios
    for s in range(len(stages)):
        path_s = path + stages[s] + '/'
        for root, dirs, files in os.walk(path_s):
            dic[int(stages[s])] = [f for f in files if not f[0] == '.']
    return dic
#%% Main function to coordinate the script
def main(data_path,step_length,param_path):
    dic_yr_in_steps, full_steps = 
    dec_dic = get_scen(param_path)
#%% If run as script
if __name__ == '__main__':
    path_param = '../../data/scenarios/'
    path_data = '../data/utopia.txt'
    step_length = 5
    main(path_data,step_length,path_param)