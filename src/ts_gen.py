"This script is part of the OSeMOSYS_step function and allows the script to handle inputs for scenarios without the indication of years but a growth rate. The script takes the growth rate and the value of the decision parameter of the last year of the previous step."
#%% Import of required packages
import pandas as pd
import main_ms as mm #for testing
#%% Main function
"The main function receives the dataframe with the parameter information that should go into a datapackage..."
def main(df,dic_yrs,path_data,step):
    df = mm.get_scen('../data/scenarios/')[2]['E'] #for testing
    df = df[df['OPTION']==0]
    dic_yrs = {0: pd.DataFrame({'VALUE': [1990,1991]}), 1: pd.DataFrame({'VALUE': [1991,1992,1993,1994,1995,1996,1997,1998,1999,2000]}), 2: pd.DataFrame({'VALUE': [1996,1997,1998,1999,2000,2001,2002,2003,2004,2005]})} #for testing
    path_data = '../data/step2/C0E0/C0' #for testing
    step = 2 #for testing
    scens = '/'.join(path_data.split('/')[3:-1])
    path_data_ps = '../data/step%(step)s/%(scens)s' % {'step': step-1, 'scens': scens}
    df_w = df[df['YEAR'].isnull()]
    for p in df_w['PARAMETER'].unique():
        for t in df_w['TECHNOLOGY'].unique():
            df_para_ps = pd.read_csv(path_data_ps+'/'+p+'.csv')
            print(t)
    return