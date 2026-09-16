import subprocess
import os
import sys

def run_cmd(args):
    print(f"Executing: {' '.join(args)}")
    res = subprocess.run(args, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    print("STDOUT:", res.stdout)
    print("STDERR:", res.stderr)
    print("RETURNCODE:", res.returncode)
    return res

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "status":
        run_cmd(["git", "status"])
        run_cmd(["git", "tag"])
        run_cmd(["python", "--version"])
