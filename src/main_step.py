# main script to run the step function of OSeMOSYS
#%% Importe required packages
import os
import subprocess as sp
import time
from otoole import ReadDatapackage
from otoole import WriteDatafile
from otoole import Context
import data_split
import step_to_final as stf
import results_to_next_step as rtns
#%% Input
path_data = '../data/utopia.txt'
step_length = 5
#%% Convert datapackage to datafile
def dp_to_df(dp_path,step):
    # otoole datapackage to datafile
    reader = ReadDatapackage()
    writer = WriteDatafile()
    converter = Context(read_strategy=reader, write_strategy=writer)
    df_path = '../data/step%s.txt' % str(step)
    converter.convert(dp_path,df_path)
    return df_path
#%% Run model
def run_df(path,step):
    results_path = '../steps/step'+str(step)
    try:
        os.mkdir(results_path)
    except OSError:
        print("Creation of the directory %s failed" %results_path)
    with open('../model/osemosys.txt', 'r') as file:
        model = file.readlines()
    rp = "param ResultsPath, symbolic default '../steps/step"+str(step)+"';\n"
    model[55] = rp
    with open('../model/osemosys.txt', 'w') as file:
        file.writelines(model)
    cd_run = 'glpsol -m ../model/osemosys.txt -d ../data/step%s.txt' % str(step)
    sp.run([cd_run],shell=True,capture_output=True)
    return results_path
#%% If run as script
if __name__ == '__main__':
    dic_yr_in_steps,full_steps = data_split.split_dp(path_data,step_length)
    df_step0 = dp_to_df('../data/datapackage0',0)
    # Run step 0
    results0 = run_df(df_step0,0)
    stf.main('../steps/step','../results/',0,dic_yr_in_steps[0].iloc[:step_length])
    print('Step 0: done')
    for s in range(full_steps):
        step = s+1
        dp_path = '../data/datapackage'+str(step)
        dp_d_path = '../data/datapackage'+str(step)+'/data'
        fr_path = '../results'
        rtns.main(dp_d_path,fr_path)
        #print('Step %s: ResCap in datapackage'%step)
        df_path = dp_to_df(dp_path,step)
        #print('Step %s: datafile created'%step)
        sr_path = run_df(df_path,step)
        #print('Step %s: model run completed'%step)
        stf.main('../steps/step','../results/',step,dic_yr_in_steps[step].iloc[:step_length])
        print('Step %s: done'%step)
# %%
