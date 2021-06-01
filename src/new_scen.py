"This script modifies an OSeMOSYS datapackage based on a provided one changing provided parameter"
#%% Import needed packages
import pandas as pd
import os
import ts_gen as tg
#import main_ms as mm #for testing
#%% Main function to coordinate the script
def main(path_data,step,dic_dec,dic_scen_dec,dic_yrs):
    # path_data = '../data/step2/C0E0/C0' #for testing
    # step = 2 #for testing
    # dic_dec = mm.get_scen('../data/scenarios/')[2] #for testing
    # dic_scen_dec =  {'C': '0','E':'0'} #for testing
    # dic_yrs = {0: pd.DataFrame({'VALUE': [1990,1991]}), 1: pd.DataFrame({'VALUE': [1991,1992,1993,1994,1995,1996,1997,1998,1999,2000]}), 2: pd.DataFrame({'VALUE': [1996,1997,1998,1999,2000,2001,2002,2003,2004,2005]})} #for testing
    for d in dic_dec: # iterate over decisions
        for p in dic_dec[d]['PARAMETER'].unique(): #iterate over parameter in decision
            for dp in range(step,len(dic_yrs)): #iterate over steps
                path_p = path_data+'/datapackage'+str(dp)+'/data/'+p+'.csv'
                df = pd.DataFrame()
                df = pd.read_csv(path_p)
                df_in = dic_dec[d][dic_dec[d]['OPTION']==int(dic_scen_dec[d])]
                df_in = df_in.rename(columns={df_in.columns[2]:df.columns[1]})
                if len(df_in['YEAR'][df_in['YEAR'].isnull()])>0:
                    df_in = tg.main(df_in,dic_yrs,path_data,step,dp)
                df_in = df_in[df_in['YEAR'].isin(dic_yrs[dp]['VALUE'])]
                if df.empty:
                    df_in = df_in[list(df.columns)]
                    df = df.append(df_in)
                else:
                    df_new = df
                    for t in df_in[df_in.columns[2]].unique():
                        df_t = df[df[df_in.columns[2]]==t]
                        df_in_ex = df_in[df_in['YEAR'].isin(df_t['YEAR'].unique())]
                        df_in_ex = df_in_ex[df_in_ex[df_in.columns[2]]==t]
                        df_in_ex = df_in_ex.set_index(df_t.index)
                        df_new.update(df_in_ex)
                        df_in_new = df_in[(df_in[df_in.columns[2]]==t)&(~df_in['YEAR'].isin(df_in_ex['YEAR'].unique()))]
                        df_new = df_new.append(df_in_new, ignore_index=True)
                    df_new = df_new.drop(columns=['PARAMETER','OPTION'])
                    df = df_new
                df.to_csv(path_p, index=False)

#%% If run as script
#if __name__ == '__main__':
    