from sys import argv
from utils import distance_matrix, generate_students, kosaraju
from random import sample
from pprint import pprint
from collections import Counter

N = 80
L = 200
MAXW = 0.002
DEPOTS = N-1
CAPACITY = 50

with open(argv[1], 'r') as f:
    g = eval(f.readline())

vset = sample(list(g), k=N)
dm, path = distance_matrix(g, vset)
students = generate_students(L,vset,MAXW)
depots = sample(range(1, N), k=DEPOTS)

resg = {i: {j: (dm[vset[i]][vset[j]], path[vset[i]][vset[j]]) for j in range(len(dm))} for i in range(len(dm))}

with open(argv[2], 'w') as f:
    f.write(str(vset) + '\n')
    f.write(str(students) + '\n')
    f.write(str(MAXW) + '\n')
    f.write(str(depots) + '\n')
    f.write(str(CAPACITY) + '\n')
    f.write(str(resg) + '\n')
