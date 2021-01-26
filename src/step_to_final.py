# script to write step results to final results
#%% Import of needed packages
import os
import pandas as pd
#%% Read results of step and filter to years in step
def read_step_res(path,yr_in_step):  
    import pandas as pd #for testing
    path = '../steps/step0/' #for testing
    yr_in_step = pd.DataFrame([1990,1991,1992,1993,1994],columns=['VALUE']) #for testing
    result_files = next(os.walk(path))
    dic_res_step = dict()
    for i in range(len(result_files[2])):
        if result_files[2][i] != 'SelectedResults.csv':
            dic_res_step[result_files[2][i]] = pd.read_csv(path+'/'+result_files[2][i])
            if 'YEAR' in dic_res_step[result_files[2][i]].columns:
                df = dic_res_step[result_files[2][i]]
                m = df.YEAR.isin(yr_in_step.VALUE)
                df = df[m]
                dic_res_step[result_files[2][i]] = df
    return dic_res_step
#%% Read final results
def read_res_final(path):
    #%% Check if provided directory is correct and contains data
    if os.path.exists(path) and os.path.isdir(path):
        if not os.listdir(path):
            print("Directory is empty")
    else:
        print("Given directory doesn't exist")
    return dic_res_final
#%% Append step results to final results
def step_to_final(res_step,res_final):

    return 
#%% Write final results to directory
def write_res(res_final):
    return
#%% Main function to coordinate the script
def main(path_step,path_final,step,yr_in_step):
    path_step_res = path_step+str(step)
    dic_step = read_step_res(path_step_res,yr_in_step)

#%% If run as a script
if __name__ == '__main__':
    path_res_step = '../steps/step'
    path_res_final = '../results'
    step = 0
    yr_in_step = pd.DataFrame([1990,1991,1992,1993,1994],columns=['VALUE'])
    main(path_res_step,path_res_final,step,yr_in_step)