# main script to run the step function of OSeMOSYS
#%% Importe required packages
import os
import subprocess as sp
from otoole import ReadDatapackage
from otoole import WriteDatafile
from otoole import Context
import data_split
import step_to_final as stf
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
    cd_run = 'glpsol -m ../model/osemosys.txt -d ../data/step%s.txt' % str(step)
    sp.run([cd_run],shell=True)
    return results_path
#%% If run as script
if __name__ == '__main__':
    dic_yr_in_steps,full_steps = data_split.split_dp(path_data,step_length)
    df_step0 = dp_to_df('../data/datapackage0',0)
    # Run step 0
    results0 = run_df(df_step0,0)
    stf.main('../steps/step','../results/',0,dic_yr_in_steps[0].iloc[:step_length])
    for s in range(full_steps): # iterate over steps from 1 till n
        step = s+1
        #put results from previous step into data of next step
        # run model
        # add results of step to final results

# %%
