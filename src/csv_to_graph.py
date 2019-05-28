import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import Counter, defaultdict
from sys import argv
from pprint import pprint
from utils import kosaraju
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--if", dest="in_file")
parser.add_option("--of", dest="out_file")
parser.add_option("--barrio", dest="barrio_str")
(options, args) = parser.parse_args()

streets = pd.read_csv(options.in_file)

streets = streets[['WKT', 'nomoficial', 'alt_izqini', 'alt_izqfin', \
                   'alt_derini', 'alt_derfin', 'sentido', 'long', 'BARRIO', \
                   'BARRIO_PAR', 'BARRIO_IMP']]

barrio = streets[(streets.BARRIO == options.barrio_str) |
                 (streets.BARRIO_PAR == options.barrio_str) |
                 (streets.BARRIO_IMP == options.barrio_str)]

print("FILTRADO BARRIO", options.barrio_str)
graph = defaultdict(lambda : {})
edge_count = 0
for index, row in barrio.iterrows():
    line = row.WKT
    # print(line)
    coords = [tuple(map(float, m.split(' ')))
              for m in re.findall(r'-?\d+.\d+ -?\d+.\d+', line)]
    if row.sentido == 'CRECIENTE':
        graph[coords[0]][coords[-1]] = (row.long, coords)
        edge_count += 1
    elif row.sentido == 'DECRECIENTE':
        graph[coords[-1]][coords[0]] = (row.long, coords[::-1])
        edge_count += 1
    elif row.sentido == 'DOBLE':
        graph[coords[0]][coords[-1]] = (row.long, coords)
        graph[coords[-1]][coords[0]] = (row.long, coords[::-1])
        edge_count += 2


add = {}
for v1, v2s in graph.items():
    for v2 in v2s:
        if v2 not in graph:
            add[v2] = {}
graph.update(add)
print("CREADO GRAFO CON", len(graph), "ESQUINAS")
print("                ", edge_count, "ARISTAS")

assignment = kosaraju(graph)
c = Counter([v for k, v in assignment.items()])
mc = c.most_common(1)[0][0]
deadends = [v for v in graph if assignment[v] != mc]

for v in deadends:
    edge_count -= len(graph[v])
    del graph[v]
for v in graph:
    des = []
    for v2 in deadends:
        if v2 in graph[v]:
            del graph[v][v2]
            edge_count -= 1
print("FILTRADO DE CALLES SIN SALIDA:", len(graph), "ESQUINAS")
print("                              ", edge_count, "ARISTAS")

# pprint(graph)
with open(options.out_file, 'w') as f:
    f.write(str(dict(graph)))
