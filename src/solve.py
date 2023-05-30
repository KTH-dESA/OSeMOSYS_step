"""Module to hold solving logic"""

from typing import Union
from pathlib import Path 
import sys 
import logging 
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
    pass

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
    pass