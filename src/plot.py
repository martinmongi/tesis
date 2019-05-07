import matplotlib.pyplot as plt
from sys import argv
from pprint import pprint
from utils import transpose

COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

if len(argv) > 3:
    with open(argv[3], 'r') as f:
        g = eval(f.readline())
        for v in g:
            for v2 in g[v]:
                plt.plot([p[0] for p in g[v][v2][1]],
                        [p[1] for p in g[v][v2][1]], '-', color='0.75')

with open(argv[1], 'r') as f:
    ls = f.readlines()
    stops = eval(ls[0])
    students = eval(ls[1])
    max_walk_dist = eval(ls[2])
    depots = eval(ls[3])
    g = eval(ls[4])

plt.plot([stops[0][0]], [stops[0][1]], 'gs')
plt.plot([stops[dep][0] for dep in depots],
         [stops[dep][1] for dep in depots], 'y^')
plt.plot([stops[i][0] for i in range(1,len(stops)) if i not in depots],
         [stops[i][1] for i in range(1,len(stops)) if i not in depots], 'ro')
plt.plot([s[0] for s in students], [s[1] for s in students], '.')

if len(argv) > 2:
    with open(argv[2], 'r') as f:
        ls = f.readlines()
        # for i in range(len(depots)):
        g_out = eval(ls[0])
        gt = transpose(g_out)
        # pprint(g_out)
        # pprint(gt[0])
        i = 0
        for v in gt[0]:
            plt.plot([p[0] for p in gt[0][v]],
                    [p[1] for p in gt[0][v]],
                    color=COLORS[i % len(COLORS)])
            while len(gt[v]) > 0:
                # pprint(v)
                # pprint(gt[v])
                v2 = next(iter(gt[v]))
                plt.plot([p[0] for p in gt[v][v2]],
                        [p[1] for p in gt[v][v2]],
                        color=COLORS[i % len(COLORS)])
                v = v2
            i += 1
        stdict = eval(ls[-1])
        for k, v in stdict.items():
            # plt.plot([students[k][0], stops[v][0]], [students[k][1], stops[v][1]])
            pass
plt.show()
