import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import Counter, defaultdict
from sys import argv
from pprint import pprint
from utils import kosaraju


streets = pd.read_csv(argv[1])

streets = streets[['WKT', 'nomoficial', 'alt_izqini', 'alt_izqfin', \
                   'alt_derini', 'alt_derfin', 'sentido', 'long', 'BARRIO', \
                   'BARRIO_PAR', 'BARRIO_IMP']]

barrio_str = argv[2]
barrio = streets[(streets.BARRIO == barrio_str) |
                 (streets.BARRIO_PAR == barrio_str) |
                 (streets.BARRIO_IMP == barrio_str)]

vertices = []
graph = defaultdict(lambda : {})
for index, row in barrio.iterrows():
    line = row.WKT
    # print(line)
    coords = [tuple(map(float, m.split(' ')))
              for m in re.findall(r'-?\d+.\d+ -?\d+.\d+', line)]
    vertices.append(coords[0])
    vertices.append(coords[-1])
    if row.sentido == 'CRECIENTE':
        graph[coords[0]][coords[-1]] = (row.long, coords)
    elif row.sentido == 'DECRECIENTE':
        graph[coords[-1]][coords[0]] = (row.long, coords[::-1])
    elif row.sentido == 'DOBLE':
        graph[coords[0]][coords[-1]] = (row.long, coords)
        graph[coords[-1]][coords[0]] = (row.long, coords[::-1])


add = {}
for v1, v2s in graph.items():
    for v2 in v2s:
        if v2 not in graph:
            add[v2] = {}
graph.update(add)

assignment = kosaraju(graph)
c = Counter([v for k, v in assignment.items()])
mc = c.most_common(1)[0][0]
deadends = [v for v in graph if assignment[v] != mc]

for v in deadends:
    del graph[v]
for v in graph:
    des = []
    for v2 in deadends:
        graph[v].pop(v2, None)

# pprint(graph)
with open(argv[3], 'w') as f:
    f.write(str(dict(graph)))
