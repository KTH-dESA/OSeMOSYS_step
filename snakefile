SOLVER = ['gurobi']
PATH_DF = ['data/step0.txt']
PATH_RES = ['steps/step0']
#FORMATS = ["txt"]

rule run_model:
    input: 
        solver = SOLVER[0],
        df_path = expand("{path}", path=PATH_DF),
#        df_path = "../data/{path_df,.+\d\.txt}"
        res_path = expand("{path}", path=PATH_RES) 
    output:
        expand("{path}.txt", path=PATH_RES}#, ext=FORMATS) 
    shell:
        "python src/solv.py {input.solver} {input.df_path} {input.res_path}"