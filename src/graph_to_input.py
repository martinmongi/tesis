from utils import generate_students
from random import sample
from pprint import pprint
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--if", dest="in_file")
parser.add_option("--of", dest="out_file")
parser.add_option("--N", "--stops", dest="N")
parser.add_option("--S", "--students", dest="S")
parser.add_option("--MAXW", "--max_walking_distance", dest="MAXW")
parser.add_option("--K", "--depots", dest="K")
parser.add_option("--C", "--capacity", dest="CAPACITY")
(options,args) = parser.parse_args()

N = int(options.N)
S = int(options.S)
MAXW = float(options.MAXW)
K = int(options.K)
CAPACITY = int(options.CAPACITY)

with open(options.in_file, 'r') as f:
    g = eval(f.readline())

vset = sample(list(g), k=N)
students = generate_students(S,vset,MAXW)
depots = sample(vset[1:], k=K)

with open(options.out_file, 'w') as f:
    f.write(str(g) + '\n')
    f.write(str(vset) + '\n')
    f.write(str(students) + '\n')
    f.write(str(MAXW) + '\n')
    f.write(str(depots) + '\n')
    f.write(str(CAPACITY) + '\n')
