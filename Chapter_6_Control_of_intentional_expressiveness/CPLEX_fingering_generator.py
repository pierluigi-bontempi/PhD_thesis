import cplex
from cplex.exceptions import CplexError
import subprocess
from docplex.mp.model import Model
from docplex.mp.context import Context


def solve_with_cplex():
    mod_file = 'CPLEX_model.mod'
    dat_file = 'CPLEX_data_file.dat'

    command = f"oplrun -v {mod_file} {dat_file}"
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
        else:
            output = result.stdout

    except Exception as e:
        print(f"CPLEX execution error: {e}")