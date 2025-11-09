import sys
from varname.helpers import exec_code

script_path = sys.argv[1]

with open(script_path) as f:
    code = f.read()

exec_code(code)