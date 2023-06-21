"""Utility functions"""

import os
import shutil
from pathlib import Path 
from typing import Dict, Any, List, Union, Tuple
from yaml import load 
import pandas as pd
import sys
import glob
from otoole.utils import UniqueKeyLoader
from otoole import ReadDatafile, WriteCsv, Context, ReadCsv

import logging
logger = logging.getLogger(__name__)

def check_for_directory(directory: Path):
    """Creates Directory 
    
    Args: 
        directory: Path
            Path to directory
    """
    if os.path.exists(directory) and os.path.isdir(directory):
        if not os.listdir(directory):
            logger.info(f"{directory} exists and is empty")
    else:
        logger.info(f"{directory} doesn't exist")
        
def read_otoole_config(config: str) -> Dict[str,Any]:
    """Reads in otoole configuration file"""
    ending = Path(config).suffix
    if ending != (".yaml" or ".yml"):
        logger.error(f"otoole config file must have a .yaml extension. Identified a {ending} extension") 
    with open(config, "r") as f:
        contents = load(f, Loader=UniqueKeyLoader)
    return contents

def format_step_input(steps: Tuple) -> List[int]:
    """Checks for proper formatting of step input"""
    for s in steps:
        if not isinstance(s, int):
            logger.warning(f"Step must be of type int. Recieved type {type(s)} for step {s}")
    if len(steps) > 2:
        logger.error(f"Step must be less than 2 values. Recieved length of {len(steps)}")
        sys.exit()
    
    return [int(s) for s in steps]

def copy_csvs(src: str, dst: str) -> None:
    """Copies directories of CSV data
        
    Args:
        src: str
            Source directory 
        dst: str
            Destination directory 
    """
    for f in os.listdir(src):
        source_file = os.path.join(src, f)
        dst_file = os.path.join(dst, f)
        shutil.copy(source_file, dst_file)
        
def get_subdirectories(directory: str):
    """Gets all subdirectories"""
    subdirectories = []
    directory_path = Path(directory)
    for path in directory_path.iterdir():
        if path.is_dir():
            if check_for_subdirectory(str(path)):
                subdirectories.extend(get_subdirectories(path))
            else:
                subdirectories.append(path)
            
    return subdirectories

def check_for_subdirectory(directory: str):
    """Checks if there is a subdirectory present"""
    directory_path = Path(directory)
    for path in directory_path.iterdir():
        if path.is_dir():
            return True
    return False

def concat_dataframes(src: pd.DataFrame, dst: pd.DataFrame, years: list[int] = None) -> pd.DataFrame:
    """Combines two dfs together
    
    Args:
        src: str, 
            first df
        dst: str, 
            Second df
        years: list[int] = None 
            Years to filter source over. If none, no filtering happens
            
    Returns:
        pd.DataFrame
            dataframes concatanted 
    """
    if not (src.columns.to_list()) == (dst.columns.to_list()):
        logger.error(f"columns for source are {src.columns} and columns to destination are {dst.columns}")
        print("Exiting...")
        sys.exit()
    if years:
        if "YEAR" in src.columns:
            src = src.loc[src["YEAR"].isin(years)].reset_index(drop=True)
    df = pd.concat([dst, src])
    if all(param in df.columns.to_list() for param in ["REGION", "TECHNOLOGY", "YEAR"]):
        df = df.sort_values(by = ["REGION", "TECHNOLOGY", "YEAR"])
    elif all(param in df.columns.to_list() for param in ["REGION", "YEAR"]):
        df = df.sort_values(by = ["REGION", "YEAR"])
    return df

def get_options_from_path(file_path: str, extension: str = None) -> Union[List[str], None]:
    """Parses a path to return options
    
    Args:
        file_path: str
            directory path 
            
    Returns:
        Options based on looking for step_*/ in the filepath 
    
    Example:
        >>> get_options_from_path("../steps/step_4/1E0-1C1/2D1/model.sol")
        >>> ["1E0-1C1", "2D1"]
    """
    if extension:
        dirs = [part for part in Path(file_path).parts if not part.endswith(extension)]
    else:
        dirs = [part for part in Path(file_path).parts if not part.endswith(extension)]
    for num, dir in enumerate(dirs):
        if dir.startswith("step_"):
            return dirs[num + 1:]
    return None
    
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
    
def read_csv(csv_dir: str, config: Dict[str,Any]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
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