import sys

sys.path.insert(0, ".")

script_path = sys.argv[1]

with open(script_path) as f:
    code = f.read()

exec(code)