import os
import subprocess
import sys

cwd = os.getcwd()
directory = cwd + "\\" + sys.argv[1] + "\\"
print(cwd)
files = os.listdir(directory)
for filename in files:
    if filename.endswith(".in"):
        barrio = directory + filename.split("_")[0] + ".g"
        print(filename)
        subprocess.run(["python", ".\\plot.py", "--if", directory +
                        filename,  "--graph", barrio])
        if filename[:-3] + ".out" in files:
            print(filename, filename[:-3] + ".out")
            subprocess.run(["python", ".\\plot.py", "--if", directory +
                            filename,  "--graph", barrio,
                            "--of", directory + filename[:-3] + ".out"])
