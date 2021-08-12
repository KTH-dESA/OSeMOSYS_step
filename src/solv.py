"This script conducts the runs of OSeMOSYS models within the OSeMOSYSstep function in cases another solver than glpk is selected"
#%% Import of needed packages
import os
import subprocess as sp
import gurobipy
from otoole import ReadGurobi
from otoole import ReadDatafile
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
    str_cmd = 'glpsol -m '+os.path.join('"..','model','osemosys.txt"')+ ' -d "%(data)s" --wlp "%(lp)s" --check' % {'data': path_df, 'lp': path_lp}
    sp.run(str_cmd,shell=True,capture_output=True)
    return path_lp
#%% Function to solve lp file using gurobi
def sol_gurobi(path_lp,path_res):
    # path_lp = '../data/step2/C0E0/C1.lp' #for testing
    # path_res = '../steps/step2/C0E0/C1' #for testing
    path_script = os.path.dirname(os.path.realpath(__file__))
    path_pkg = os.path.join(' ', os.sep.join(path_script.split(os.sep)[:-1]))
    path_issue = path_res + '.ilp'
    path_issue_abs = os.path.join(path_pkg, os.sep.join(path_issue.split(os.sep)[1:]))
    path_sol = path_res + '.sol'
    path_sol_abs = os.path.join(path_pkg, os.sep.join(path_sol.split(os.sep)[1:]))
    path_lp_abs = os.path.join(path_pkg, os.sep.join(path_lp.split(os.sep)[1:]))
    m = gurobipy.read(path_lp_abs)
    m.optimize()
    m.write(path_sol_abs)
    if not os.stat(path_sol_abs).st_size > 0:
        m.computeIIS()
        m.write(path_issue_abs)
    # str_cmd = 'gurobi_cl ResultFile=%(issue)s ResultFile=%(solution)s "%(lp)s"' % {'issue': path_issue_abs,'solution': path_sol_abs,'lp': path_lp_abs}
    # sp.run(str_cmd,shell=True,capture_output=True)
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
def csv_gurobi(path_sol,path_res,p_df):
    #path_sol = '../data/step0.sol' #for testing
    #path_res = '../data/res' #for testing
    reader = ReadGurobi()
    writer = WriteCsv()
    input_data, _ = ReadDatafile().read(p_df)
    converter = Context(read_strategy=reader,write_strategy=writer)
    converter.convert(path_sol,path_res,input_data=input_data)
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
            csv_gurobi(path_sol,path_res,path_df)
#%% If run as script
#if __name__ == '__main__':
