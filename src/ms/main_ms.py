"This script is the main script for running multi-scenario (ms) multi-stage OSeMOSYS models"
#%% Import required packages
import pandas as pd
import os
#%% Function to derive scenario information from provided folders and files
def get_scen(path):
    path = '../../data/scenarios/' #for testing
    stages = next(os.walk(path))[1]
    dec_dic = dict()
    for s in range(len(stages)):
        path_s = path + stages[s] + '/'
        for root, dirs, files in os.walk(path_s):
            dec_dic[int(stages[s])] = [f for f in files if not f[0] == '.']
    return
#%% Main function to coordinate the script
def main():

#%% If run as script
if __name__ == '__main__':
