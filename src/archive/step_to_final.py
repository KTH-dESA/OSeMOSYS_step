# script to write step results to final results
#%% Import of needed packages
import logging as log
import os
import pandas as pd
import shutil
import sys
#%% Read results of step and filter to years in step
def read_step_res(path,yr_in_step):  
    result_files = next(os.walk(path))
    dic_res_step = dict()
    for i in range(len(result_files[2])):
        if result_files[2][i] != 'SelectedResults.csv' and result_files[2][i] != 'TotalTechnologyModelPeriodActivity':
            dic_res_step[result_files[2][i]] = pd.read_csv(path+'/'+result_files[2][i])
            if 'YEAR' in dic_res_step[result_files[2][i]].columns:
                df = dic_res_step[result_files[2][i]]
                m = df.YEAR.isin(yr_in_step.VALUE)
                df = df[m]
                dic_res_step[result_files[2][i]] = df
    return dic_res_step
#%% Read final results
def read_res_final(path):
# Check if provided directory is correct and contains data
    path = os.path.join(path,'res')
    if os.path.exists(path) and os.path.isdir(path):
        if not os.listdir(path):
            log.info("%s is empty" % path)
    else:
        log.warning("%s doesn't exist" % path)
    final_res_files = next(os.walk(path))
    dic_res_final = dict()
    for i in range(len(final_res_files[2])):
        dic_res_final[final_res_files[2][i]] = pd.read_csv(os.path.join(path,final_res_files[2][i]))
    return dic_res_final
#%% Append step results to final results
def step_to_final(res_step,res_final):
    dic_final = res_final
    for df in dic_final:
        if df in res_step:
            dic_final[df] = dic_final[df].append(res_step[df],ignore_index=True)
    return dic_final
#%% Write final results to directory
def write_res(path,res_final):
    path = os.path.join(path,'res')
    try:
        os.mkdir(path)
    except OSError:
        print("Creation of the directory %s failed" %path)
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            log.warning("Failed to delete %s. Reason: %s" (file_path,e))
    for df in res_final:
        res_final[df].to_csv(os.path.join(path,df),index=False)
    return
#%% Main function to coordinate the script
def main(path_step_res,path_final,step,yr_in_step):
    dic_step = read_step_res(path_step_res,yr_in_step)
    if step > 0:
        dic_old_final = read_res_final(path_final)
        dic_new_final = step_to_final(dic_step,dic_old_final)
        write_res(path_final,dic_new_final)
    else:
        write_res(path_final,dic_step)

#%% If run as a script
if __name__ == '__main__':
    path_res_step = '../steps/step'
    path_res_final = '../results/'
    step = sys.argv[1]
    yr_in_step = sys.argv[2]
    main(path_res_step,path_res_final,step,yr_in_step)
# %%
