from math import fabs
from collections import defaultdict

def dist(x,y):
    return ((x[0] - y[0])**2 + (x[1] - y[1])**2)**.5

def mann_dist(x,y):
    return fabs(x[0] - y[0]) + fabs(x[1] - y[1])


def graphs(vnames, vals, depots, g):
    res = []
    dsol = {vnames[i]: vals[i] for i in range(len(vals))}
    for bn in depots:
        res.append(defaultdict(lambda: []))
        for v1 in g:
            for v2 in g[v1]:
                if dsol["bus_edge_" + str(bn) + "_" + str(v1) + "_" + str(v2)] > 0.5:
                    res[-1][v1].append(v2)
    return res
