"""utility functions for the main script"""

from typing import Dict, List, Tuple, Any
import pandas as pd
import os
from pathlib import Path
import logging
import utils
import subprocess
from otoole import WriteDatafile
from otoole import ReadCsv
from otoole import Context

logger = logging.getLogger(__name__)

def get_step_data(scenaro_path: str) -> Dict[int, Dict[str, pd.DataFrame]]:
    """Get step information 
    
    Args: 
        scenaro_path: str
    
    Returns:
        Dict[int, Dict[str, pd.DataFrame]]
    
    Example:
    If scenarios are arranged as: 
        
        scenarios/
            1/
                A.csv
                B.csv
            2/
                C.csv
    
    The funtion will return 
    
        {
            1:{A:pd.DataFrame, B:pd.DataFrame,},
            2:{C:pd.DataFrame}
        }   
    """
    steps = next(os.walk(scenaro_path))[1] # returns subdirs in scenarios/
    scenarios_per_step = {}
    for step_num in steps:
        step_path = Path(scenaro_path, step_num)
        scenario_data = {}
        for _, _, files in os.walk(str(step_path)):
            scenarios = [f for f in files if not f[0] == '.'] 
        for scenario in scenarios:
            # the -4 removes the .csv
            scenario_data[scenario[:-4]] = pd.read_csv(Path(step_path, scenario))
        scenarios_per_step[int(step_num)] = scenario_data
        
    return scenarios_per_step

def make_step_directories(path: str, num_steps: int) -> Dict[int, List[str]]:
    """Create folder for each step and a dictonary with their paths
    
    Args:
        path: str
            path to suffix of file 
        steps: List[int]
            Number of steps
            
    Returns 
        Dict[int, str]
        
    Example
        >>> make_step_directories("data/", 3)
        >>> ls data
        >>> data/step1, data/step2, data/step3
    """
    
    dic_step_paths = {}
    for step in range(num_steps):
        path_step = os.path.join(path, f"step_{step}")
        dic_step_paths[step] = [path_step]
        try:
            os.mkdir(path_step)
        except OSError:
            print(f"Creation of the directory {path_step} failed")
    return dic_step_paths

def get_options_per_step(steps: Dict[int, Dict[str, pd.DataFrame]]) -> Dict[int, List[List[str]]]:
    """Create a dictionary of options for each step 
    
    Args: 
        steps: Dict[int, Dict[str, pd.DataFrame]]
            steps dictionary 
    
    Returns: 
        Dict[int, List[str]]
        
    Example: 
        >>> get_options_per_step( .. )
        >>> {0: [], 1:[A0-B0, A0-B1, A1-B0, A1-B1], 2:[C0, C1]}
    """
    options_per_step = {}
    for step, scenarios in steps.items():
        
        # create all the combinations 
        options_per_scenario = get_options_per_scenario(scenarios) # {A:[0,1], B:[1,2,3], C:[0]}
        grouped_options = []
        if len(options_per_scenario) == 1:
            for scenario, options in options_per_scenario.items():
                for option in options:
                    grouped_options.append(f"{scenario}{option}")
            options_per_step[int(step)] = grouped_options
        else:
            for scenario, options in options_per_scenario.items():
                for next_scenario, next_options in options_per_scenario.items():
                    if next_scenario == scenario:
                        continue
                    for option in options:
                        for next_option in next_options:
                            grouped_options.append([f"{scenario}{option}",f"{next_scenario}{next_option}"])
            grouped_options = remove_duplicate_combinations(grouped_options)
            expanded_options = ["-".join(x) for x in grouped_options] 
            options_per_step[int(step)] = expanded_options
    
    return options_per_step

def get_option_data(steps: Dict[int, Dict[str, pd.DataFrame]]) -> Dict[str, pd.DataFrame]:
    """Gets option data in DataFrames. 
    
    This function does NOT return an index over steps, but rater options (A0, A1 ...)
    
    Args: 
        steps: Dict[int, Dict[str, pd.DataFrame]]
            steps dictionary 
            
    Returns: 
        Dict[str, pd.DataFrame]
            Options dictionary 
    
    Example: 
        >>> get_option_data(steps)
        >>> {
            A0: pd.DataFrame,
            A1: pd.DataFrame,
            B0: pd.DataFrame,
        }
    """
    
    option_data = {}
    for step, scenarios in steps.items():
        for scenario, df in scenarios.items():
            for option in df['OPTION'].unique():
                option_data[f"{scenario}{option}"] = df.loc[df["OPTION"] == option].reset_index(drop=True)
    return option_data
    
def remove_duplicate_combinations(options: List[Tuple]) -> List[Tuple]:
    """Removes duplicate options from each step
    
    Args:
        options: List[Tuple]
            List of tuples
    
    Returns: 
        combinations: List[Tuple]
            List of tuples
            
    Example:
        >>> remove_duplicate_combinations([(A0, A1), (A0, B0), (A0, B1), (A1, B0), (A1, B1)])
        >>> [(A0, B0), (A0, B1), (A1, B0), (A1, B1)]
    """
    
    unique_options = []
    for option in options:
        option_set = set(option)
        if option_set not in [set(x) for x in unique_options]:
            unique_options.append(option)
    return unique_options

def get_option_combinations_per_step(options_per_step: Dict[int, List[List[str]]]) -> Dict[int, List[str]]:
    """Gets full permutations of file paths in each step
    
    Args:
        options_per_step: Dict[int, List[str]]
            {1:[A0-B0, A0-B1, A1-B0, A1-B1], 2:[C0, C1]}
        
    returns:
        {
            0: [],
            1:[[A0-B0], [A0-B1], [A1-B0], [A1-B1]],
            2:[
                [A0-B0,C0], [A0-B1,C0], [A1-B0,C0], [A1-B1,C0],
                [A0-B0,C1], [A0-B1,C1], [A1-B0,C1], [A1-B1,C1]
            ]
        }
    """
    
    option_combos_per_step = {}
    max_step = max(list(options_per_step))
    for step_num in range(0, max_step):
        current_step = step_num
        last_step = current_step - 1
       
       # first step
        if current_step == 0: 
            option_combos_per_step[0] = options_per_step[0]
            continue
        
        # no new options for this step
        if not options_per_step[current_step]:
            option_combos_per_step[current_step] = option_combos_per_step[last_step][:]
            continue
        
        # no options for previous step 
        if not options_per_step[last_step]:
            option_combos_this_step = []
            for current_step_option in options_per_step[current_step]:
                option_combos_this_step.append([current_step_option])
            option_combos_per_step[current_step] = option_combos_this_step
            continue

        # permutate in new options
        option_combos_this_step = []
        for last_step_option in options_per_step[last_step]:
            for current_step_option in options_per_step[current_step]:
                option_combos_this_step.append([last_step_option, current_step_option])
        option_combos_per_step[current_step] = option_combos_this_step
    
    return option_combos_per_step

def get_options_per_scenario(scenarios: Dict[str, pd.DataFrame]) -> List[str]:
    """Gets list of all options per scenario

    Args: 
        step: Dict[str, pd.DataFrame]
            scenarios in a step

    Returns
        All scenario/option mappings 
    
    Example:
    >>> get_options(scenarios)
    >>> {A:[0,1], B:[1,2,3], C:[0]}
    """
    options = {}
    for scenario, df in scenarios.items():
        options[scenario] = df['OPTION'].unique().tolist()
    return options 

def create_option_directories(root_dir: str, options_per_step: Dict[int, List[str]], step_directories: bool = True) -> None:
    """Create directories at the option level
    
    Args: 
        root_dir: str
            Root dirctory to expand options directories
        options_per_step: Dict[int, List[str]]
            All options per step 
        step_directories: bool = True
            Nest options under step directories 
    """
    
    option_combos = get_option_combinations_per_step(options_per_step)
    max_step = max(list(options_per_step))
    for step_num in range(0, max_step):
        
        if step_num not in list(option_combos):
            logger.info(f"No scenario data for step {step_num}")
            continue

        # step has no options
        # combos = list(option_combos[step_num])
        if not option_combos[step_num]:
            new_dirs = []
        else:
            new_dirs = option_combos[step_num]

        # no options 
        if not new_dirs:
            new_dir_copy = []
            if step_directories:
                new_dir_copy.insert(0, f"step_{step_num}")
            new_dir_copy.insert(0, root_dir)
            dir_path = Path(*new_dir_copy)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory {str(dir_path)}")
        
        else: 
            for new_dir in new_dirs:
                new_dir_copy = new_dir[:]
                if step_directories:
                    new_dir_copy.insert(0, f"step_{step_num}")
                new_dir_copy.insert(0, root_dir)
                dir_path = Path(*new_dir_copy)
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory {str(dir_path)}")
        
def copy_reference_option_data(src_dir: str, dst_dir: str, options_per_step: Dict[int, List[str]]) -> None:
    """Copies original data to step/option folders
    
    Args: 
        src_dir: str
            Root data folder 
        dst_dir: str
            Root destination folder
        options_per_step: Dict[int, List[str]]
            All options per step 
    """
    
    option_combos = get_option_combinations_per_step(options_per_step)
    max_step = max(list(options_per_step))
    for step_num in range(0, max_step):
        if step_num not in list(option_combos):
            logger.info(f"No scenario data for step {step_num}")
            continue
        if not option_combos[step_num]:
            src = Path(src_dir,f"data_{step_num}")
            dst = Path(dst_dir, f"step_{step_num}")
            utils.copy_csvs(src, dst)
        for dsts in option_combos[step_num]:
            src = Path(src_dir,f"data_{step_num}")
            dst = Path(dst_dir, f"step_{step_num}", *dsts)
            utils.copy_csvs(src, dst)
        
def split_path_name(directory: str) -> List[str]:
    """Splits path name into sub directories
    
    Args:
        directory: str
            Directory to split 
    Returns: 
        List[str]
            List of subdirectories in order 
            
    Example: 
        >>> split_path_name("/path/to/directory/subdir1/subdir1a")
        >>> ['path', 'to', 'directory', 'subdir1', 'subdir1a']
    """
    directory = Path(directory)
    dirs = [str(p) for p in directory.parents]
    dirs.reverse()
    dirs.append(str(directory.name))
    return dirs

def apply_option(df: pd.DataFrame, option: pd.DataFrame) -> pd.DataFrame:
    """Applies option to dataframe
    
    Args:
        df:pd.DataFrame
            Input dataframe (original)
        option:pd.DataFrame
            Option to apply 
    
    Returns: 
        pd.DataFrame
            Updated dataframe with option applied
    """
    option_index = option.columns.to_list()
    option_index.remove(["PARAMETER", "OPTION"])
    index = df.columns.to_list()
    if option_index != index:
        logger.error(f"Option index of {option_index} does not match expected index of {index}")
    option = option[index]
    df = pd.concat([df, option])
    df = df.drop_duplicates(keep="last")
    return df


def add_missing_steps(options_per_step: Dict[int, List[str]], max_step: int) -> Dict[int, List[str]]:
    """Adds missing step information
    
    Args:
        options_per_step: Dict[int, List[str]]
            {1:[A0-B0, A0-B1, A1-B0, A1-B1], 2:[C0, C1]}
        max_step: int
        
    Returns: 
        Dict[int, List[str]]
        
    Example: 
        >>> add_missing_steps({1:[A0-B0, A0-B1, A1-B0, A1-B1], 2:[C0, C1]}, 4)
        >>> {0: [], 1:[A0-B0, A0-B1, A1-B0, A1-B1], 2:[C0, C1] 3: [], 4:[]}
    """
    for step in range(0, max_step + 1):
        try:
            _ = options_per_step[step]
        except KeyError:
            options_per_step[step] = []
    return options_per_step

def create_datafile(csv_dir: str, datafile: str, config: Dict[str,Any]) -> None:
    """Converts a folder of CSV data into a datafile 
    
    Args:
        csv_dir: str
            path to csv directory
        datafile: str
            name of datafile save location
        config: Dict[str,Any]
            otoole configuration data
    """
    reader = ReadCsv(user_config=config)
    writer = WriteDatafile(user_config=config)
    converter = Context(read_strategy=reader, write_strategy=writer)
    converter.convert(csv_dir, datafile)
    
def get_option_data_per_step(steps: Dict[int, Dict[str, pd.DataFrame]]) -> Dict[int, Dict[str, pd.DataFrame]]:
    """Gets option data at a step level.
    
    Args:
        steps: Dict[int, Dict[str, pd.DataFrame]]
            Data at a step level - see get_step_data(scenaro_path: str)
            
    Returns:
        Dict[int, Dict[str, pd.DataFrame]]
            Data at a step level, parsed by option 
            
    Example:
        >>> get_options_per_step(
                1:{A:pd.DataFrame, B:pd.DataFrame},
                2:{C:pd.DataFrame}
            )
        >>> {1: 
                {
                    A0: pd.DataFrame,
                    A1: pd.DataFrame,
                    B0: pd.DataFrame,
                }
            2: 
                {
                    B0: pd.DataFrame,
                    B1: pd.DataFrame,
                }
            }
        
    """
    step_option_data = {}
    for step, step_data in steps.items():
        step_option_data[step] = {}
        for scenario, scenario_data in step_data.items():
            options = scenario_data["OPTION"].unique()
            for option in options:
                df = scenario_data.loc[scenario_data["OPTION"] == option].reset_index(drop=True)
                step_option_data[step][f"{scenario}{option}"] = df
    return step_option_data

def get_param_data_per_option(step_option_data: Dict[int, Dict[str, pd.DataFrame]]) -> Dict[int, Dict[str, Dict[str, pd.DataFrame]]]:
    """Gets param data for each option at a step level
    
    Args:
        step_option_data: Dict[int, Dict[str, pd.DataFrame]]
            Option data at a step level -> see get_options_per_step()
            
    Returns: 
        Dict[int, Dict[str, Dict[str, pd.DataFrame]]]
            Param data per option per step
            
    Example: 
        >>> get_param_data_per_option()
        >>> {1: {A0: {TotalAnnualMaxCapacity: pd.DataFrame, TotalAnnualMaxCapacityInvestment: pd.DataFrame}}}
    """

    param_per_option_per_step_data = {}
    for step, option in step_option_data.items():
        param_per_option_per_step_data[step] = {}
        for option_name, option_data in option.items():
            params = option_data["PARAMETER"].unique()
            options = option_data["OPTION"].unique()
            for option in options:
                if not option_name.endswith(str(option)):
                    continue
                param_per_option_per_step_data[step][option] = {}
                for param in params:
                    df = option_data.drop(columns=["PARAMETER", "OPTION"])
                    param_per_option_per_step_data[step][option][param] = df
    return param_per_option_per_step_data

def results_to_next_step(next_step: int, option_path: str, parameter: str):
    #dp_path = '../tests/fixtures/data' #for testing
    #fr_path = '../tests/fixtures/results' #for testing
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
    df_out = df_out.round({'VALUE':4})
    df_out.to_csv(rc_path,index=False)
    return
        
    
    