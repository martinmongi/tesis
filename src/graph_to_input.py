from sys import argv
from utils import distance_matrix, generate_students, kosaraju
from random import sample
from pprint import pprint
from collections import Counter

N = 50
L = 200
MAXW = 0.002
DEPOTS = 2
CAPACITY = 100

with open(argv[1], 'r') as f:
    g = eval(f.readline())

vset = sample(list(g), k=N)
students = generate_students(L,vset,MAXW)
depots = sample(vset[1:], k=DEPOTS)

with open(argv[2], 'w') as f:
    f.write(str(g) + '\n')
    f.write(str(vset) + '\n')
    f.write(str(students) + '\n')
    f.write(str(MAXW) + '\n')
    f.write(str(depots) + '\n')
    f.write(str(CAPACITY) + '\n')
