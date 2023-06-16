"""Utility functions"""

import os
import shutil
from pathlib import Path 
from typing import Dict, Any, List
from yaml import load 
import pandas as pd
import sys
from otoole.utils import UniqueKeyLoader

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

def format_step_input(steps: Any) -> List[int]:
    """Checks for proper formatting of step input"""
    if not isinstance(steps, list):
        if not isinstance(steps, int):
            logger.error(f"Step must be of type int or List[int]. Recieved type {type(steps)}")
        else:
            steps = [steps]
    if len(steps) > 2:
        logger.error(f"Step must be less than 2 values. Recieved length of {len(steps)}")
    
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

def merge_dataframes(src: pd.DataFrame, dst: pd.DataFrame, years: list[int] = None) -> pd.DataFrame:
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
            Merged df
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