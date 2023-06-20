"""Module to split the input data on step years"""

import sys
import pandas as pd
import math
from otoole import ReadDatafile, ReadCsv
from otoole import WriteCsv
from otoole import Context
from typing import Dict, Tuple, List, Any
from pathlib import Path 
import utils
import logging

logger = logging.getLogger(__name__)

def datafile_to_csv(datafile: str, csv_dir: str, config: Dict[str,Any]) -> None:
    """Converts datafile to folder of csvs
    
    Args:
        datafile: str
            Path to datafile 
        csv_dir: str
            Path to directory of csv folder 
        config: Dict[str,Any]
            otoole configuration data
    """
    reader = ReadDatafile(user_config=config)
    writer = WriteCsv(user_config=config)
    converter = Context(read_strategy=reader, write_strategy=writer)
    converter.convert(datafile, csv_dir)
    
def read_csv(csv_dir: str, config: Dict[str,Any], data: bool = True) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
    """Reads in csv data using otoole
    
    Returns: 
        Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]
            First dictionary is the data 
            Second dictionary is the default values
    """
    reader = ReadCsv(user_config=config)
    return reader.read(filepath=csv_dir)

def write_csv(data: Dict[str, pd.DataFrame], default_values: Dict[str, Any], csv_dir:str, config: Dict[str,Any]) -> None:
    """Writes out CSV data"""
    writer = WriteCsv(user_config=config)
    writer.write(inputs=data, filepath=csv_dir, default_values=default_values)

def get_step_data(data: Dict[str, pd.DataFrame], years: List[int]) -> Dict[str, pd.DataFrame]:
    """Get reference csv data for each step 
    
    Note that the data is the same format as otoole; mulitindex dataframe 
    
    Args:
        data: Dict[str, pd.DataFrame]
            Complete set of reference data 
        years: List[int]
            years to filter over 
            
    Returns:
        Dict[str, pd.DataFrame]
            Filtered data over the years 
    """
    out = {}
    
    for name, df in data.items():
        if df.empty:
            out[name] = df
        elif "YEAR" in df.index.names:
            df = df.reset_index()
            cols = list(df)
            cols.remove("VALUE")
            out[name] = df.loc[df["YEAR"].isin(years)].set_index(cols)
        elif name == "YEAR":
            out[name] = df.loc[df["VALUE"].isin(years)]
        else:
            out[name] = df
            
    return out 
    
# Function to run the script
def split_data(datafile: str, step_size: List[int]) -> Tuple[Dict, int]:
    """Reads in and splits data for steps 
    
    Args: 
        datafile: str
            Path to directory
        step_size: List[int]
            Years in each step. If one value provided, equal step sizes. If 
            multiple values provided, the first values represents the first 
            step, with the remaining step sizes being the second value
    
    Returns:
        actual_years_per_step: Dict {step: actual years in step}
            Actual years per step (ie. 1995-2000 for a 5yr step)
        model_years_per_step: Dict {step: modelled years in step}
            Modelled years per step (ie. 1995-2005 for a 5yr step)
        full_steps: int
            Number of full steps in model run indexed from zero
    """
    
    # check for directory structure 
    data_dir = Path(datafile).parents[0]
    utils.check_for_directory(data_dir)
    
    # Create folder of csvs from datafile
    csv_dir = Path(data_dir, "data")
    config_path = Path(data_dir, "otoole_config.yaml") # chnage this to an input 
    config = utils.read_otoole_config(str(config_path))
    datafile_to_csv(str(datafile), str(csv_dir), config)
    
    # Derive information on modelling period
    m_period = pd.read_csv(Path(csv_dir, "YEAR.csv"))
    n_years = len(m_period.index)
    if len(step_size) < 2:
        n_steps = n_years / step_size[0]
    else:
        n_steps = 1 + (n_years - step_size[0]) / step_size[1]
    full_steps = math.floor(n_steps)
    all_steps = math.ceil(n_steps)
    
    # Read in reference csv data
    otoole_reader = read_csv(str(csv_dir), config)
    data = otoole_reader[0]
    default_values = otoole_reader[1]
    model_years_per_step = {} # actual years plus extra at end
    actual_years_per_step = {} # actual years per step 
    
    # parse out data based on number of years 
    i = 0
    if len(step_size) < 2:
        for i in range(all_steps):
            start = step_size[0] * i
            if i + 1 < full_steps:
                end_model = start + (step_size[0] * 2)
                end_actual = start + step_size[0]
                model_step_years = m_period.iloc[start:end_model]["VALUE"].to_list()
                actual_step_years = m_period.iloc[start:end_actual]["VALUE"].to_list()
            else:
                model_step_years = m_period.iloc[start:]["VALUE"].to_list()
                actual_step_years = m_period.iloc[start:]["VALUE"].to_list()
            model_years_per_step[i] = model_step_years
            actual_years_per_step[i] = actual_step_years
            step_data = get_step_data(data, model_step_years)
            write_csv(step_data, default_values, str(Path(data_dir, f"data_{i}")), config)
            logger.info(f"Wrote data for step {i}")
    else:
        for i in range(all_steps):
            if i == 0:
                start = 0
                end_model = step_size[0] * 2
                end_actual = step_size[0]
                step_years_model = m_period.iloc[start:end_model]["VALUE"].to_list()
                step_years_actual = m_period.iloc[start:end_actual]["VALUE"].to_list()
            elif i + 1 < full_steps:
                start = step_size[0] + step_size[1] * (i - 1)
                end_model = start + (step_size[1] * 2)
                end_actual = start + step_size[1]
                step_years_model = m_period.iloc[start:end_model]["VALUE"].to_list()
                step_years_actual = m_period.iloc[start:end_actual]["VALUE"].to_list()
            else:
                start = step_size[0] + (i - 1) * step_size[1]
                step_years_model = m_period.iloc[start:]["VALUE"].to_list()
                step_years_actual = m_period.iloc[start:]["VALUE"].to_list()
            model_years_per_step[i] = step_years_model
            actual_years_per_step[i] = step_years_actual
            step_data = get_step_data(data, step_years_model)
            write_csv(step_data, default_values, str(Path(data_dir, f"data_{i}")), config)
            logger.info(f"Wrote data for step {i}")
                
    return actual_years_per_step, model_years_per_step, full_steps

if __name__ == '__main__':
    path = sys.argv[1]
    step = int(sys.argv[2])
    steps = utils.format_step_input(step)
    split_data(path, steps)