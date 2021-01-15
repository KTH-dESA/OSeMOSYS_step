# main script to run the step function of OSeMOSYS
#%% Importe required packages
import os
import data_split
#%% Input
path_data = '../data/datapackage'
step_length = 5
#%% If run as script
if __name__ == '__main__':
    data_split.split_dp(path_data,step_length)
# %%
