# This script has the purpose to split the provided datapackage into several datapackages
#%%
import os
import pandas as pd
import math
#%%
path = '../data/datapackage' #for working
step = 10 # for working
#%%
if os.path.exists(path) and os.path.isdir(path):
    if not os.listdir(path):
        print("Directory is empty")
else:
    print("Given directory doesn't exist")

m_period = pd.read_csv(path+'/data/YEAR.CSV')
n_years = len(m_period.index)
n_steps = n_years/step
full_steps = math.floor(n_steps)
all_steps = math.ceil(n_steps)
i = 0
for i in range(all_steps):
    if i+1 < full_steps:
        end = (step*2)*(i+1)
        start = end - (step*2)
        step_years = m_period.iloc[start:end]
 #   else:
  #      start = i * step
   #     step_years = m_period.iloc[start:]
        
#%%
def new_dp(datapackage,years):
#%%
    datapackage = '../data/datapackage' #for development
    years = step_years # for development
    datafiles = next(os.walk(datapackage+'/data'))
    j = 0
    for j in range(len(datafiles[2])):
        
# %%
