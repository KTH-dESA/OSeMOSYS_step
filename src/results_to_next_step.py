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
    df_init = pd.read_csv(rc_path)
    df_ol = pd.read_csv(ol_path)
    df_nc = pd.read_csv(nc_path)
    df_out = df_init
    tec = pd.Series(df_init['TECHNOLOGY'].unique())
    for 
    for t in range(len(df_nc)):
        if #goal: add techs to series that are not in residual capacity but in new capacity

    return
#%% If run as script
if __name__ == '__main__':
    dp_path = '../data/datapackage1/data' #for testing
    fr_path = '../results' #for testing