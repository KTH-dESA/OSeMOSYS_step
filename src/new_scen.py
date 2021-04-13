"This script modify a OSeMOSYS datapackage based on a provided one changing provided parameter"
#%% Import needed packages
import pandas as pd
import os
import main_ms as mm #for testing
#%% Main function to coordinate the script
def main(path_data,step,dic_dec,dic_scen_dec,dic_yrs):
    path_data = '../data/step1/C0E0' #for testing
    step = 1 #for testing
    dic_dec = mm.get_scen('../data/scenarios/')[1] #for testing
    dic_scen_dec =  {'C': '0', 'E': '0'} #for testing
    dic_yrs = {0: pd.DataFrame({'VALUE': [1990,1991]}), 1: pd.DataFrame({'VALUE': [1991,1992,1993,1994,1995,1996,1997,1998,1999,2000]})}
    for d in dic_dec: # iterate over decisions
        for p in dic_dec[d]['PARAMETER'].unique(): #iterate over parameter in decision
            for dp in range(step,len(dic_yrs)): #iterate over steps
                path_p = path_data+'/datapackage'+str(dp)+'/data/'+p+'.csv'
                df = pd.read_csv(path_p)
                df_in = dic_dec[d][dic_dec[d]['OPTION']==int(dic_scen_dec[d])]
                df_in = df_in[df_in['YEAR'].isin(dic_yrs[dp]['VALUE'])]
                if df.empty:
                    df_in = df_in[list(df.columns)]
                    df = df.append(df_in)
                else:
                    df_old = df
                    for t in df_in['TECHNOLOGY'].unique():
                        df = df[df['TECHNOLOGY']==t]
                        df_in_ex = df_in[df_in['YEAR'].isin(df['YEAR'].unique())]
                        df_in_ex = df_in_ex[df_in_ex['TECHNOLOGY']==t]
                        df_in_ex = df_in_ex.set_index(df.index)
                        df_old.update(df_in_ex)
                        df_in_new = df_in[(df_in['TECHNOLOGY']==t)&(~df_in['YEAR'].isin(df_in_ex['YEAR'].unique()))]
                        df_old = df_old.append(df_in_new, ignore_index=True)
                    df = df_old
                df.to_csv(path_p, index=False)
    return
#%% If run as script
if __name__ == '__main__':
    