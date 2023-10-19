"""Module to hold solving logic"""

from typing import Union, Dict, Any
from pathlib import Path
import sys
import logging
import subprocess
import os
# from otoole import ReadCbc, ReadCplex, ReadGurobi, ReadDatafile, ReadCsv
# from otoole import WriteCsv
# from otoole import Context

from otoole import convert_results


logger = logging.getLogger(__name__)

def generate_results(sol_file: str, solver: str, config: Dict[str,Any], data_file: str = None, csv_data: str = None) -> None:
    """Converts a solution file to a folder of CSVs

    Note, only one of datafile or csv data need to be passed to generate full suit of results

    Args:
        sol_file: str
            path to sol file
        datafile: str
            name of datafile save location
        config: Dict[str,Any]
            otoole configuration data
        data_file: str
            path to data file. if not provided, the full suit of results will NOT be generated
        csv_data: str
            path to csv data. if not provided, the full suit of results will NOT be generated
    """

    sol_dir = Path(sol_file).parent

    # if solver == "gurobi":
    #     reader = ReadGurobi(user_config = config)
    # elif solver == "cplex":
    #     reader = ReadCplex(user_config = config)
    # elif solver == "cbc":
    #     reader = ReadCbc(user_config = config)
    # writer = WriteCsv(user_config = config)

    # if data_file:
    #     input_data, _ = ReadDatafile(user_config=config).read(data_file)
    # elif csv_data:
    #     input_data, _ = ReadCsv(user_config=config).read(csv_data)
    # else:
    #     input_data = None

    # context = Context(read_strategy = reader, write_strategy = writer)

    # context.convert(sol_file, str(Path(sol_dir, "results")), input_data = input_data)

    convert_results(config, solver, 'csv', sol_file, str(Path(sol_dir, "results")), 'datafile', data_file)

def create_lp(datafile: str, lp_file: str, osemosys: str, log_file:str = None) -> int:
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

    if log_file:
        cmd = f"glpsol -m {osemosys} -d {datafile} --wlp {lp_file} --check --log {log_file}"
        subprocess.run(cmd, shell = True, capture_output = True)

    else:
        cmd = f"glpsol -m {osemosys} -d {datafile} --wlp {lp_file} --check"
        subprocess.run(cmd, shell = True, capture_output = True)

    if not os.path.exists(lp_file):
        logger.error(f"Can not create {lp_file}")
        return 1
    else:
        return 0


def check_cbc_feasibility(sol: str) -> int:
    """Checks if the CBC solution is optimal

    Args:
        sol: str
            Path to CBC solution file

    Returns:
        0: int
            If successful
        1: int
            If not successful
    """
    with open(sol) as f:
        first_line = f.readline()
    status = first_line.split(" ")[0]
    if status == "Optimal":
        return 0
    else:
        return 1

def check_glpk_feasibility(sol: str) -> int:
    """Checks if the GLPK solution is optimal

    Args:
        sol: str
            Path to CBC solution file

    Returns:
        0: int
            If successful
        1: int
            If not successful

    c Problem:    osemosys
    c Rows:       3721
    c Columns:    2280
    c Non-zeros:  18069
    c Status:     OPTIMAL
    c Objective:  cost = 16068.9934 (MINimum)

    """
    fifth_line = get_nth_line(sol, 5)
    status = fifth_line.split(" ")[6]
    status = status.strip()
    if status == "OPTIMAL":
        return 0
    else:
        return 1

def check_gurobi_feasibility(sol: str) -> int:
    """Checks if the gurobi solution is optimal

    This will check for an empty solution file, not the ilp file that
    Gurobi will also write out for infeasible

    Args:
        sol: str
            Path to gurobi solution file

    Returns:
        0: int
            If successful
        1: int
            If not successful
    """
    if Path(sol).stat().st_size != 0: # not empty
        return 0
    else:
        return 1

def get_nth_line(file_path: str, n: int):
    """Gets nth line from a textfile"""
    with open(file_path, 'r') as file:
        for i, line in enumerate(file, start=1):
            if i == n:
                return line
    return None


