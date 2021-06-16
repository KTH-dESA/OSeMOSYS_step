"This script conducts the runs of OSeMOSYS models within the OSeMOSYSstep function in cases another solver than glpk is selected"
#%% Import of needed packages
import os
import subprocess as sp
from otoole import ReadGurobi
from otoole import WriteCsv
from otoole import Context
#%% Create directory for results
def create_res_dir(path_res):
    try:
        os.mkdir(path_res)
    except OSError:
        print("Creation of the directory %s failed" %path_res)
    
    return
#%% Function to create lp file
def create_lp(path_df):
    name_lp = path_df.split(os.sep)[-1].split('.')[0] + '.lp'
    path_lp = os.path.join(os.sep.join(path_df.split(os.sep)[:-1]),name_lp)
    str_cmd = 'glpsol -m '+os.path.join('..','model','osemosys.txt')+ ' -d %(data)s --wlp %(lp)s --check' % {'data': path_df, 'lp': path_lp}
    sp.run([str_cmd],shell=True,capture_output=True)
    return path_lp
#%% Function to solve lp file using gurobi
def sol_gurobi(path_lp,path_res):
    # path_lp = '../data/step2/C0E0/C1.lp' #for testing
    # path_res = '../steps/step2/C0E0/C1' #for testing
    path_issue = path_res + '.ilp'
    path_sol = path_res + '.sol'
    str_cmd = 'gurobi_cl ResultFile=%(issue)s ResultFile=%(solution)s %(lp)s' % {'issue': path_issue,'solution': path_sol,'lp': path_lp}
    sp.run([str_cmd],shell=True,capture_output=True)
    if os.path.exists(path_res+'.ilp'):
        path_sol = None
    if os.path.exists(path_lp):
        os.remove(path_lp)
    else:
        print('The file %s does not exist.' % path_lp)
    return path_sol
#%% Function to solve lp file using cbc
def sol_cbc(path_lp):
    return path_sol
#%% Function to solve lp file using cplex
def sol_cplex(path_lp):
    return path_sol
#%% 
"Function to convert gurobi sol file to csvs"
def csv_gurobi(path_sol,path_res):
    reader = ReadGurobi()
    writer = WriteCsv()
    converter = Context(read_strategy=reader,write_strategy=writer)
    converter.convert(path_sol,path_res)
    if os.path.exists(path_sol):
        os.remove(path_sol)
#%% main function
def main(solver,path_df,path_res):
    # solver ='gurobi' #for testing
    # path_df = '../data/step1/C0E0.txt' #for testing
    # path_res = '../steps/step1/C0E0' #for testing
    create_res_dir(path_res)
    path_lp = create_lp(path_df)
    if solver == 'gurobi':
        path_sol = sol_gurobi(path_lp,path_res)
        if path_sol != None:
            csv_gurobi(path_sol,path_res)
#%% If run as script
#if __name__ == '__main__':
