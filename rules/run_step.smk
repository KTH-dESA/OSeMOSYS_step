SOLVER = []
PATH_DF = []
PATH_RES = []
FORMATS = ["sol", "ilp"]

rule run_model:
    input: 
        solver = SOLVER[0],
        df_path = expand("{path}", path=PATH_DF),
#        df_path = "../data/{path_df,.+\d\.txt}"
        res_path = expand("{path}", path=PATH_RES) 
    output:
        expand("{path}/{{scenario}}.{ext}", path=PATH_RES, ext=FORMATS)
    shell:
        "python ../src/solv.py solver df_path res_path"