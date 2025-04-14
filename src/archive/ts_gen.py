"This script is part of the OSeMOSYS_step function and allows the script to handle inputs for scenarios without the indication of years but a change rate. The script takes the change rate and the value of the decision parameter of the last year of the previous step."
#%% Import of required packages
import pandas as pd
import os
import sys
# import main_ms as mm #for testing
#%% Create time series using a growth rate
def ts_rate(rate,yr,init,yr0):
    value = init * (1+rate)**(yr-yr0)
    return value
#%% Create time series using an absolute value for annual change
def ts_abs(rate,yr,init,yr0):
    value =init + rate * (yr-yr0)
    if value<0:
        value = 0
    return value
#%% Main function
"The main function receives the dataframe with the parameter information that should go into a datapackage..."
def main(df,dic_yrs,path_data,step,dp):
    # df = mm.get_scen('../data/scenarios/')[2]['E'] #for testing
    # df = df[df['OPTION']==0]
    # dic_yrs = {0: pd.DataFrame({'VALUE': [1990,1991]}), 1: pd.DataFrame({'VALUE': [1991,1992,1993,1994,1995,1996,1997,1998,1999,2000]}), 2: pd.DataFrame({'VALUE': [1996,1997,1998,1999,2000,2001,2002,2003,2004,2005]})} #for testing
    # path_data = '../data/step2/C0E0/C0' #for testing
    # step = 2 #for testing
    # dp = 2 #for testing
    if step==0:
        sys.exit('It seems you provided a change rate for a decision parameter in step 0. This is not possible since no previous value for the parameter is available. Please indicate the options for the decision parameter in step 0 with time series.')
    if dp == step:
        scens = os.sep.join(path_data.split(os.sep)[3:-1])
        path_data_ps = '../data/step%(step)s/%(scens)s/datapackage%(dp_p)s/data' % {'step': step-1, 'scens': scens, 'dp_p': dp-1}
    else:
        scens = os.sep.join(path_data.split(os.sep)[3:])
        path_data_ps = '../data/step%(step)s/%(scens)s/datapackage%(dp_p)s/data' % {'step': step, 'scens': scens, 'dp_p': dp-1}
    last_yr_ps = dic_yrs[dp]['VALUE'].min()-1
    df_w = df[df['YEAR'].isnull()]
    col = list(df_w.columns)
    df_out = pd.DataFrame(columns=col)
    for p in df_w['PARAMETER'].unique():
        for r in df_w['REGION'].unique():
            for t in df_w[df_w.columns[2]].unique():
                df_para_ps = pd.read_csv(os.path.join(path_data_ps,p)+'.csv')
                if len(df_para_ps[df_para_ps['YEAR']==last_yr_ps])==0:
                    sys.exit('Seems like you are providng a change rate for a parameter that has not been defined before or that is at least not defined in the last year of the previous step. For parameter that have not been defined before, please provide in the first step where the paremter is to be defined a time series.')
                last_value_ps = df_para_ps.loc[df_para_ps[(df_para_ps['YEAR']==last_yr_ps)&(df_para_ps.iloc[:,1]==t)].index.tolist()[0]]['VALUE']
                change = df_w.loc[df_w[(df_w['PARAMETER']==p)&(df_w[df_w.columns[2]]==t)].index.tolist()[0]]['VALUE']
                if str(change)[-1]=='%': # check if change is a growth rate or an absolute value
                    change = float(change[:-1])/100
                    for y in dic_yrs[dp]['VALUE']:
                        value = ts_rate(change,y,last_value_ps,last_yr_ps)
                        df_out = df_out.append(pd.DataFrame([[p,r,t,df_w['OPTION'].unique()[0],y,value]],columns=col),ignore_index=True)
                else:
                    for y in dic_yrs[dp]['VALUE']:
                        value = ts_abs(change,y,last_value_ps,last_yr_ps)
                        df_out = df_out.append(pd.DataFrame([[p,r,t,df_w['OPTION'].unique()[0],y,value]],columns=col),ignore_index=True)
    return df_out