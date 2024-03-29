# This script has the purpose to split the provided datapackage into several datapackages
#%% Needed packages
import sys
import os
from shutil import copyfile
import subprocess as sp
import pandas as pd
import math
import time
from otoole import ReadDatafile
from otoole import WriteDatapackage
from otoole import Context
#%% Convert datafile to datapackage
def df_to_dp(path):
    #path = '../data/utopia.txt' #for development
    #file = '/utopia.txt' #for development
    dp_path = '../data/datapackage'
    os.mkdir(dp_path)
    reader = ReadDatafile()
    writer = WriteDatapackage()
    converter = Context(read_strategy=reader, write_strategy=writer)
    converter.convert(path, dp_path)
    return dp_path
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
def new_dp(dp_dic,years,step_nr,path):
    #dic = dp_dic #for development
    #years = step_years # for development
    #step_nr = 1 # for development
    path = path+str(step_nr)
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" % path)
    copyfile('../data/datapackage/datapackage.json',path+'/datapackage.json')
    path = path + '/data'
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
            df.to_csv(path+'/'+i,index=False)
        elif i=='YEAR.csv':
            df = dp_dic[i]
            m = df.VALUE.isin(years.VALUE)
            df = df[m]
            df.to_csv(path+'/'+i,index=False)
        else:
            df = dp_dic[i]
            df.to_csv(path+'/'+i,index=False)
    while not os.path.exists(path+'/YearSplit.csv'):
        time.sleep(5)
    #Write csv for param ResultsPath, might need adjustment depending on implementation of ResultsPath in otoole
#    rp_csv = pd.Series(['VALUE','../steps/step'+str(step_nr)])
#    rp_csv.to_csv(path+'/ResultsPath.csv',index=False,header=False)
#%% Function to run the script
def split_dp(directory,step_size):
    #%% Check if provided directory is correct and contains data
    if os.path.exists(directory) and os.path.isdir(directory):
        if not os.listdir(directory):
            print("Directory is empty")
    else:
        print("Given directory doesn't exist")
    # Create datapackage from datafile
    dp_path = df_to_dp(directory)
    # Derive information on modelling period
    m_period = pd.read_csv(dp_path+'/data/YEAR.csv')
    n_years = len(m_period.index)
    if type(step_size)==int:
        n_steps = n_years/step_size
    else:
        n_steps = 1+(n_years-step_size[0])/step_size[1]
    full_steps = math.floor(n_steps)
    all_steps = math.ceil(n_steps)
    # Read in datapackage
    dp_dic = read_dp(dp_path)
    dic_yr_step = dict()
    i = 0
    if type(step_size)==int:
        for i in range(all_steps):
            if i+1 < full_steps:
                start = step_size * i
                end = start+(step_size*2)
                step_years = m_period.iloc[start:end]
                dic_yr_step[i] = step_years
                new_dp(dp_dic,step_years,i,dp_path)
            else:
                start = i * step_size
                step_years = m_period.iloc[start:]
                dic_yr_step[i] = step_years
                new_dp(dp_dic,step_years,i,dp_path)
    else:
        for i in range(all_steps):
            if i==0:
                start = 0
                end = step_size[0]*2
                step_years = m_period.iloc[start:end]
                dic_yr_step[i] = step_years
                new_dp(dp_dic,step_years,i,dp_path)
            elif i+1 < full_steps:
                start = step_size[0] + step_size[1] * (i-1)
                end = start+(step_size[1]*2)
                step_years = m_period.iloc[start:end]
                dic_yr_step[i] = step_years
                new_dp(dp_dic,step_years,i,dp_path)
            else:
                start = step_size[0] + (i-1) * step_size[1]
                step_years = m_period.iloc[start:]
                dic_yr_step[i] = step_years
                new_dp(dp_dic,step_years,i,dp_path)
    return dic_yr_step,full_steps
#%% data_split executed as script
if __name__ == '__main__':
    #%% Inputs
    #path = '../data/utopia.txt' #for developing
    #step = [6,10] # for developing
    path = sys.argv[1]
    step = sys.argv[2]
    dic_yr_step = split_dp(path,step)