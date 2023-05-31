"""Module to hold solving logic"""

from typing import Union, Dict, Any
from pathlib import Path 
import sys 
import logging
import subprocess
import os 
from otoole import ReadCbc, ReadCplex, ReadGurobi
from otoole import WriteCsv
from otoole import Context
logger = logging.getLogger(__name__)

def solve(lp_file: str, sol_dir: str, solver: Union[str, None]) -> int:
    """Calls solving logic"""
    
    if not solver:
        exit_code = solve_glpk(lp_file, sol_dir)
    elif solver == "gurobi":
        sol_file = Path(sol_dir, "solution.sol")
        exit_code = solve_gurobi(lp_file, sol_file)
    elif solver == "cplex":
        sol_file = Path(sol_dir, "solution.sol")
        exit_code = solve_cplex(lp_file, sol_file)
    elif solver == "cbc":
        sol_file = Path(sol_dir, "solution.sol")
        exit_code = solve_cbc(lp_file, sol_file)
    else:
        logger.warning(f"Solver selection of {solver} is not valid")
        sys.exit()
    return exit_code
    

def solve_glpk(lp_file: str, sol_dir: str) -> int:
    """Solves using GLPK
    
    Args:
        lp_file: str, 
        sol_dir: str
    
    Returns:
        0: int
            If successful 
        1: int
            If not successful
    """
    pass

def solve_cbc(lp_file: str, sol_file: str) -> int:
    """Solves using CBC
    
    Args:
        lp_file: str, 
        sol_file: str
    
    Returns:
        0: int
            If successful 
        1: int
            If not successful
    """
    raise NotImplementedError

def solve_gurobi(lp_file: str, sol_file: str) -> int:
    """Solves using Gurobi
    
    Args:
        lp_file: str, 
        sol_file: str
    
    Returns:
        0: int
            If successful 
        1: int
            If not successful
    """
    pass

def solve_cplex(lp_file: str, sol_file: str) -> int:
    """Solves using Gurobi
    
    Args:
        lp_file: str, 
        sol_file: str
    
    Returns:
        0: int
            If successful 
        1: int
            If not successful
    """
    raise NotImplementedError

def generate_results(sol_file: str, solver: str, config: Dict[str,Any]) -> None:
    """Converts a solution file to a folder of CSVs
    
    Args:
        csv_dir: str
            path to csv directory
        datafile: str
            name of datafile save location
        config: Dict[str,Any]
            otoole configuration data
    """
    
    sol_dir = Path(sol_file).parent
    
    if solver == "gurobi":
        reader = ReadGurobi(user_config=config)
    elif solver == "cplex":
        reader = ReadCplex(user_config=config)
    elif solver == "cbc":
        reader = ReadCbc(user_config=config)
    writer = WriteCsv(user_config=config)
    converter = Context(read_strategy=reader, write_strategy=writer)
    
    converter.convert(sol_file, str(sol_dir))
    
def create_lp(datafile: str, lp_file: str, osemosys: str) -> int:
    """Create the LP file using GLPK
    
    Args: 
       datafile: str, 
       lp_file: str, 
       osemosys: str 
       
    Returns:
        0: int
            If successful 
        1: int
            If not successful
    """
    cmd = f"glpsol -m {osemosys} -d {datafile} --wlp {lp_file} --check"

    subprocess.run(cmd, shell = True, capture_output = True)
    
    if not os.path.exists(lp_file):
        logger.warning(f"Can not create {lp_file}")
        return 1
    else:
        return 0