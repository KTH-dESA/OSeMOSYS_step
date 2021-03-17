# This script passes the needed results from one step to the next one
#%% Import needed packages
import pandas as pd
#%% Main function to coordinate the script
def main(dp_path,fr_path):
    dp_path = '../data/datapackage1/data' #for testing
    fr_path = '../results' #for testing
    rc_path = dp_path +'/ResidualCapacity.csv'
    ol_path = dp_path +'/OperationalLife.csv'
    nc_path = fr_path +'/NewCapacity.csv'
    yr_path = dp_path +'/YEAR.csv'
    df_init = pd.read_csv(rc_path)
    df_ol = pd.read_csv(ol_path)
    df_nc = pd.read_csv(nc_path)
    df_yr = pd.read_csv(yr_path)
    df_out = df_init
    tec = pd.Series(df_init['TECHNOLOGY'].unique())
    tec = tec.append(pd.Series(df_nc['TECHNOLOGY'][~df_nc.TECHNOLOGY.isin(tec)].unique()),ignore_index=True)
    tec = tec[tec.isin(df_ol['TECHNOLOGY'])]
    for t in tec:
        for y in df_yr['VALUE']:
            df = df_nc
            df = df[df['TECHNOLOGY']==t]
            ol = df_ol.loc[df_ol.loc[df_ol['TECHNOLOGY']==t].index[0],'VALUE']
            df = df[df['YEAR']>(y-ol)]
            

    return
#%% If run as script
if __name__ == '__main__':
    dp_path = '../data/datapackage1/data' #for testing
    fr_path = '../results' #for testing