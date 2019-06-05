from random import sample, choice, uniform
from utils import haversine_dist
from pprint import pprint
from optparse import OptionParser


def generate_students(n, stops, max_w):
    max_w_deg = max_w / 78710
    students = []
    for _ in range(n):
        st = choice(stops[1:])
        while True:
            std = (uniform(st[0] - max_w_deg, st[0] + max_w_deg),
                   uniform(st[1] - max_w_deg, st[1] + max_w_deg))
            if haversine_dist(std, st) <= max_w:
                break
        students.append(std)
    return students

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
