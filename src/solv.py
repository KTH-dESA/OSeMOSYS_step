"This script conducts the runs of OSeMOSYS models within the OSeMOSYSstep function in cases another solver than glpk is selected"
#%% Import of needed packages
import gurobipy
import logging as log
import os
from otoole import ReadGurobi
from otoole import ReadDatafile
from otoole import WriteCsv
from otoole import Context
import subprocess as sp
import sys
#%% Create directory for results
def create_res_dir(path_res):
    try:
        os.mkdir(path_res)
    except OSError:
        log.info("%s couldn't be created" %path_res)
    
    return
#%% Function to create lp file
def create_lp(path_df):
    name_lp = path_df.split(os.sep)[-1].split('.')[0] + '.lp'
    path_lp = os.path.join(os.sep.join(path_df.split(os.sep)[:-1]),name_lp)
    str_cmd = 'glpsol -m '+os.path.join('"..','model','osemosys.txt"')+ ' -d "%(data)s" --wlp "%(lp)s" --check' % {'data': path_df, 'lp': path_lp}
    sp.run(str_cmd,shell=True,capture_output=True)
    if not os.path.exists(path_lp):
        log.warning("%s couldn't be created" % path_lp)
    return path_lp
#%% Function to solve lp file using gurobi
def sol_gurobi(path_lp,path_res, scen_info):
    path_script = os.path.dirname(os.path.realpath(__file__))
    path_pkg = os.path.join(' ', os.sep.join(path_script.split(os.sep)[:-1]))
    path_issue = path_res + '.ilp'
    path_issue_abs = os.path.join(path_pkg, os.sep.join(path_issue.split(os.sep)[1:]))
    path_sol = path_res + '.sol'
    path_sol_abs = os.path.join(path_pkg, os.sep.join(path_sol.split(os.sep)[1:]))
    path_lp_abs = os.path.join(path_pkg, os.sep.join(path_lp.split(os.sep)[1:]))
    m = gurobipy.read(path_lp_abs)
    m.optimize()
    try:
        m.write(path_sol_abs)
        log.info("%s written" % path_sol)
    except:
        m.computeIIS()
        m.write(path_issue_abs)
    if os.path.exists(path_res+'.ilp'):
        path_sol = None
        os.remove(path_sol_abs)
    if os.path.exists(path_lp):
        os.remove(path_lp)
    else:
        log.warning('%s does not exist.' % path_lp)

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
    reader = ReadGurobi()
    writer = WriteCsv()
    input_data, _ = ReadDatafile().read(p_df)
    converter = Context(read_strategy=reader,write_strategy=writer)
    converter.convert(path_sol,path_res,input_data=input_data)
    if os.path.exists(path_sol):
        os.remove(path_sol)
#%% main function
def main(solver,path_df_prep,path_res):
    scen_sep = '|'
    scen_info = scen_sep.join(path_res.split(os.sep)[2:])
    path_log = os.path.join('..','results','solv_logs', scen_info+'.log')
    log.basicConfig(filename=path_log, level=log.INFO)
    create_res_dir(path_res)
    path_df = path_df_prep.split('_')[0] + '.txt'
    path_lp = create_lp(path_df_prep)
    if os.path.exists(path_lp):
        if solver == 'gurobi':
            path_sol = sol_gurobi(path_lp,path_res, scen_info)
            if path_sol != None:
                csv_gurobi(path_sol,path_res,path_df)
    path_complete = path_res + '.txt'
    file_done = open(path_complete, "w")
    file_done.close()
#%% If run as script
if __name__ == '__main__':
    solver = str(sys.argv[1])
    path_df = str(sys.argv[2])
    path_res = str(sys.argv[3])
    main(solver, path_df, path_res)