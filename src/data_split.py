# This script has the purpose to split the provided datapackage into several datapackages
#%% Needed packages
import sys
import os
import pandas as pd
import math
#%% Inputs
#path = '../data/datapackage' #for developing
#step = 5 # for developing

path = sys.argv[1]
step = sys.argv[2]
#%% Check if provided directroy is correct and contains data
if os.path.exists(path) and os.path.isdir(path):
    if not os.listdir(path):
        print("Directory is empty")
else:
    print("Given directory doesn't exist")
#%% Derive information on modelling period
m_period = pd.read_csv(path+'/data/YEAR.CSV')
n_years = len(m_period.index)
n_steps = n_years/step
full_steps = math.floor(n_steps)
all_steps = math.ceil(n_steps)

#%% Read in csv files from datapackage
def read_dp(dp_path):
    #dp_path = '../data/datapackage' #for development
    datafiles = next(os.walk(dp_path+'/data'))
    dic = dict()
    j = 0
    for j in range(len(datafiles[2])):
        dic[datafiles[2][j]] = pd.read_csv(dp_path+'/data/'+datafiles[2][j])
    return dic
#%% Create new csv files from original csvs
def new_dp(dic,years,step_nr):
    #dic = dp_dic #for development
    #years = step_years # for development
    #step_nr = 1 # for development
    path = '../data/datapackage'+str(step_nr)
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)

    i = 0
    for i in dp_dic:
        if 'YEAR' in dp_dic[i].columns:
            df = dp_dic[i]
            m = df.YEAR.isin(years.VALUE)
            df = df[m]
            df.to_csv(path+'/'+i)
        else:
            df = dp_dic[i]
            df.to_csv(path+'/'+i)
#%%
dp_dic = read_dp(path)
i = 0
for i in range(all_steps):
    if i+1 < full_steps:
        start = step * i
        end = start+(step*2)
        step_years = m_period.iloc[start:end]
        new_dp(dp_dic,step_years,i)
    else:
        start = i * step
        step_years = m_period.iloc[start:]
        new_dp(dp_dic,step_years,i)