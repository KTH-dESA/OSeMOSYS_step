#%%
import pandas as pd
#%% Get technologies
def get_techs(path):
    df = pd.read_csv(path)
    return df
#%% Main function
def main():
    tech_path = '../../OSeMBE_dev/input_data/REF/data/TECHNOLOGY.csv'
    techs = get_techs(tech_path)
    return techs
if __name__ == '__main__':
    tec = main()