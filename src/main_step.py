# main script to run the step function of OSeMOSYS
#%% Importe required packages
import sys
import os
import subprocess as sp
import time
from otoole import ReadDatapackage
from otoole import WriteDatafile
from otoole import Context
import data_split
import step_to_final as stf
import results_to_next_step as rtns
#%% Convert datapackage to datafile
def dp_to_df(dp_path,df_path):
    # otoole datapackage to datafile
    reader = ReadDatapackage()
    writer = WriteDatafile()
    converter = Context(read_strategy=reader, write_strategy=writer)
    converter.convert(dp_path,df_path)
#%% Run model
def run_df(path,results_path):
    try:
        os.mkdir(results_path)
    except OSError:
        print("Creation of the directory %s failed" %results_path)
    with open('../model/osemosys.txt', 'r') as file:
        model = file.readlines()
    rp = "param ResultsPath, symbolic default '"+results_path+"';\n"
    model[55] = rp
    with open('../model/osemosys.txt', 'w') as file:
        file.writelines(model)
    cd_run = 'glpsol -m ../model/osemosys.txt -d %s' % path
    sp.run([cd_run],shell=True,capture_output=True,check=True)
    return results_path
#%% Main function to coordinate the execution of the script
def main(path_data,step_length):
    if type(step_length)==int:
        dic_yr_in_steps,full_steps = data_split.split_dp(path_data,step_length)
        df_step0 = '../data/step0.txt'
        dp_to_df('../data/datapackage0',df_step0)
        res_path = '../steps/step'+str(0)
        # Run step 0
        run_df(df_step0,res_path)
        stf.main('../steps/step0','../results/',0,dic_yr_in_steps[0].iloc[:step_length])
        print('Step 0: done')
        for s in range(full_steps):
            step = s+1
            df_path = '../data/step'+str(step)+'.txt'
            dp_path = '../data/datapackage'+str(step)
            dp_d_path = '../data/datapackage'+str(step)+'/data'
            fr_path = '../results'
            rtns.main(dp_d_path,fr_path)
            #print('Step %s: ResCap in datapackage'%step)
            dp_to_df(dp_path,df_path)
            #print('Step %s: datafile created'%step)
            res_path = '../steps/step'+str(step)
            run_df(df_path,res_path)
            #print('Step %s: model run completed'%step)
            stf.main('../steps/step'+str(step),'../results/',step,dic_yr_in_steps[step].iloc[:step_length])
            print('Step %s: done'%step)
    else:
        dic_yr_in_steps,full_steps = data_split.split_dp(path_data,step_length)
        df_step0 = '../data/step0.txt'
        dp_to_df('../data/datapackage0',df_step0)
        # Run step 0
        res_path = '../steps/step'+str(0)
        run_df(df_step0,res_path)
        stf.main('../steps/step0','../results/',0,dic_yr_in_steps[0].iloc[:step_length[0]])
        print('Step 0: done')
        for s in range(full_steps):
            step = s+1
            df_path = '../data/step'+str(step)+'.txt'
            dp_path = '../data/datapackage'+str(step)
            dp_d_path = '../data/datapackage'+str(step)+'/data'
            fr_path = '../results'
            rtns.main(dp_d_path,fr_path)
            #print('Step %s: ResCap in datapackage'%step)
            dp_to_df(dp_path,df_path)
            #print('Step %s: datafile created'%step)
            res_path = '../steps/step'+str(step)
            run_df(df_path,res_path)
            #print('Step %s: model run completed'%step)
            stf.main('../steps/step'+str(step),'../results/',step,dic_yr_in_steps[step].iloc[:step_length[1]])
            print('Step %s: done'%step)
#%% If run as script
if __name__ == '__main__':
    path_data = '../data/utopia.txt'
    step_length = [6,10]
    #path_data = sys.argv[1]
    #step_length = sys.argv[2]
    main(path_data,step_length)
# %%
