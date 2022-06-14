# This script passes the needed results from one step to the next one
#%% Import needed packages
import pandas as pd
import sys
import os
#%% Main function to coordinate the script
def main(dp_path,fr_path):
    #dp_path = '../data/datapackage1/data' #for testing
    #fr_path = '../results' #for testing
    rc_path = os.path.join(dp_path,'ResidualCapacity.csv')
    ol_path = os.path.join(dp_path,'OperationalLife.csv')
    nc_path = os.path.join(fr_path,'res','NewCapacity.csv')
    yr_path = os.path.join(dp_path,'YEAR.csv')
    df_init = pd.read_csv(rc_path)
    df_ol = pd.read_csv(ol_path)
    df_nc = pd.read_csv(nc_path)
    df_yr = pd.read_csv(yr_path)
    df_out = df_init
    tec = pd.Series(df_init['TECHNOLOGY'].unique())
    tec = tec.append(pd.Series(df_nc['TECHNOLOGY'][~df_nc.TECHNOLOGY.isin(tec)].unique()),ignore_index=True)
    tec = tec[tec.isin(df_ol['TECHNOLOGY'])]
    for r in df_nc['REGION'].unique():
        for t in tec:
            for y in df_yr['VALUE']:
                df = df_nc
                df = df[df['TECHNOLOGY']==t]
                ol = df_ol.loc[df_ol.loc[df_ol['TECHNOLOGY']==t].index[0],'VALUE']
                df = df[((y+1)>df['YEAR'])&(df['YEAR']>(y-ol))]
                if len(df_out[(df_out['TECHNOLOGY']==t)&(df_out['YEAR']==y)]) > 0 :
                    i = df_out.loc[(df_out['TECHNOLOGY']==t)&(df_out['YEAR']==y)].index[0]
                    df_out.loc[i,'VALUE'] = df_out.loc[i,'VALUE'] + df['VALUE'].sum()
                else:
                    df_out = df_out.append(pd.DataFrame([[r,t,y,df['VALUE'].sum()]],columns=['REGION','TECHNOLOGY','YEAR', 'VALUE']),ignore_index=True)
    df_out.to_csv(rc_path,index=False)
    return
#%% If run as script
if __name__ == '__main__':
    #dp_path = '../data/datapackage1/data' #for testing
    #fr_path = '../results' #for testing
    dp_path = sys.argv[1]
    fr_path = sys.argv[2]
    main(dp_path,fr_path)