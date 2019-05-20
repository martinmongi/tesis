import matplotlib.pyplot as plt
from sys import argv
from pprint import pprint
from utils import transpose, ProblemData
from pprint import pprint

COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

if len(argv) > 1:
    with open(argv[1], 'r') as f:
        g = eval(f.readline())
        for v in g:
            for v2 in g[v]:
                path = g[v][v2][1]
                plt.plot([p[0] * 1000 for p in path],
                        [p[1] * 1000 for p in path], '-', color='0.8')
                plt.arrow(path[-2][0] * 1000,
                        path[-2][1] * 1000,
                        (path[-1][0] - path[-2][0]) * 1000 / 2,
                        (path[-1][1] - path[-2][1]) * 1000 / 2, head_width=0.2, head_length=.2, color='0.8')
        

if len(argv) > 2:
    data = ProblemData(argv[2])
    for v in data.original_graph:
        for v2 in data.original_graph[v]:
            path = data.original_graph[v][v2][1]
            plt.plot([p[0] * 1000 for p in path],
                        [p[1] * 1000 for p in path], '-', color='0.6')
            plt.arrow(path[-2][0] * 1000,
                        path[-2][1] * 1000,
                        (path[-1][0] - path[-2][0]) * 1000 / 2,
                        (path[-1][1] - path[-2][1]) * 1000 / 2, head_width=0.2, head_length=.2, color='0.6')
    plt.plot([data.stops[0][0] * 1000],
             [data.stops[0][1] * 1000], 'gh', markersize=20)
    plt.plot([dep[0] * 1000 for dep in data.depots],
             [dep[1] * 1000 for dep in data.depots], 'y^', markersize=20)
    plt.plot([s[0] * 1000 for s in data.stops[1:] if s not in data.depots],
             [s[1] * 1000 for s in data.stops[1:] if s not in data.depots], 'ro')
    plt.plot([s[0] * 1000 for s in data.students], [s[1] * 1000
                                                    for s in data.students], '.')

if len(argv) > 3:
    with open(argv[3], 'r') as f:
        ls = f.readlines()
        for i in range(len(ls) - 1):
            g = eval(ls[i])
            for v1 in g:
                for v2 in g[v1]:
                    plt.plot([p[0] * 1000 + (i-(len(ls)-1)//2) * 0.1 for p in g[v1][v2]],
                             [p[1] * 1000 + (i-(len(ls)-1)//2) * 0.1 for p in g[v1][v2]],
                             color=COLORS[i % len(COLORS)])
        # assignment = eval(ls[-1])
        # # for st, s in assignment.items():
        # #     plt.plot([p[0] * 1000 for p in [st, s]],
        # #              [p[1] * 1000 for p in [st, s]])
plt.show()
