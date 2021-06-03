#%%
import pandas as pd
#%% Get technologies
def get_techs(path):
    df = pd.read_csv(path)
    return df
#%% Filter technologies to needed ones
def filter_tec(df,token):
    #df = techs #for testing
    #token = 'CS' #for testing
    df['TECHNOLOGY'] = df['VALUE'].str.slice(start=4,stop=6)
    df_new = df[df['TECHNOLOGY'].str.contains(token)]
    df_new = df_new['VALUE'].reset_index(drop=True)
    return df_new
#%% create series for years
def gen_yrs(start_yr,end_yr):
    yrs = pd.Series(name='YEAR')
    for y in range(start_yr,end_yr+1):
        yrs = yrs.append(pd.Series([y]),ignore_index=True)
    return yrs
#%%
def generate_scen_df(df_techs,param,reg,years,dic_opt):

    return df
#%% Main function
def main(tec_path,tec_filter,regs,yr_s,yr_e,dic_ops):
    #tec_path = '../../OSeMBE_dev/input_data/REF/data/TECHNOLOGY.csv' #for testing
    #tec_filter = 'CS' #for testing
    techs = get_techs(tec_path)
    techs_selec = filter_tec(techs,tec_filter)
    years = gen_yrs(yr_s,yr_e)
    
    return years
#%%
if __name__ == '__main__':
    tech_path = '../../OSeMBE_dev/input_data/REF/data/TECHNOLOGY.csv'
    tech_filter = 'CS'
    regions = ['REGION1']
    parameter = 'TotalAnnualMaxCapacityInvestment'
    year_start = 2021
    year_end = 2060
    dict_options = {'0': 0, '1': 99999}
    tec = main(tech_path,tech_filter,regions,year_start,year_end,dict_options)