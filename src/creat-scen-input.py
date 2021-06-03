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
#%%

#%% Main function
def main(tec_path,tec_filter):
    #tec_path = '../../OSeMBE_dev/input_data/REF/data/TECHNOLOGY.csv' #for testing
    #tec_filter = 'CS' #for testing
    techs = get_techs(tec_path)
    techs_selec = filter_tec(techs,tec_filter)
    return techs_selec
#%%
if __name__ == '__main__':
    tech_path = '../../OSeMBE_dev/input_data/REF/data/TECHNOLOGY.csv'
    tech_filter = 'CS'
    tec = main(tech_path,tech_filter)