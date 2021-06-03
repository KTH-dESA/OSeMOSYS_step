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
def generate_scen_df(df_techs,param,reg,ys,dic_opt):
    df = pd.DataFrame([],columns=['PARAMETER','REGION','TECHNOLOGY','OPTION','YEAR','VALUE'])
    for r in reg:
        df_r = pd.DataFrame([],columns=['PARAMETER','REGION','TECHNOLOGY','OPTION','YEAR','VALUE'])
        for o in dic_opt:
            df_o = pd.DataFrame([],columns=['PARAMETER','REGION','TECHNOLOGY','OPTION','YEAR','VALUE'])
            for t in df_techs:
                df_t = pd.DataFrame([],columns=['PARAMETER','REGION','TECHNOLOGY','OPTION','YEAR','VALUE'])
                df_t['YEAR'] = ys
                df_t['PARAMETER'] = param
                df_t['REGION'] = r
                df_t['TECHNOLOGY'] = t
                df_t['OPTION'] = o
                df_t['VALUE'] = dic_opt[o]
                df_o = df_o.append(df_t, ignore_index=True)
            df_r = df_r.append(df_o, ignore_index=True)
        df = df.append(df_r,ignore_index=True)
    return df
#%% Main function
def main(param,tec_path,tec_filter,regs,yr_s,yr_e,dic_ops):
    #tec_path = '../../OSeMBE_dev/input_data/REF/data/TECHNOLOGY.csv' #for testing
    #tec_filter = 'CS' #for testing
    techs = get_techs(tec_path)
    techs_selec = filter_tec(techs,tec_filter)
    years = gen_yrs(yr_s,yr_e)
    df = generate_scen_df(techs_selec,param,regs,years,dic_ops)
    return df
#%%
if __name__ == '__main__':
    tech_path = '../../OSeMBE_dev/input_data/REF/data/TECHNOLOGY.csv'
    tech_filter = 'CS'
    regions = ['REGION1']
    parameter = 'TotalAnnualMaxCapacityInvestment'
    year_start = 2021
    year_end = 2060
    dict_options = {'0': 0, '1': 99999}
    tec = main(parameter,tech_path,tech_filter,regions,year_start,year_end,dict_options)