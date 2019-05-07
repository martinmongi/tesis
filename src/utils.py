from math import fabs
from collections import defaultdict, Counter, deque
from random import choice, uniform
from itertools import combinations_with_replacement
import matplotlib.pyplot as plt
from heapq import heappop, heappush
import sys
from pprint import pprint

class ProblemData:
    def __init__(self, filename):
        with open(filename + '.in', 'r') as f:
            ls = f.readlines()
            self.stops = eval(ls[0])
            self.N = len(self.stops)
            self.vertices = range(self.N)
            self.edges = [
                (i, j) for i in range(self.N) for j in range(self.N) if i != j]
            self.students = eval(ls[1])
            self.L = len(self.students)
            self.max_walk_dist = eval(ls[2])
            self.student_to_stop = {
                k: [v for v in range(1, len(self.stops))
                    if dist(self.stops[v],
                            self.students[k]) <= self.max_walk_dist]
                for k in range(len(self.students))}
            self.stop_to_student = {
                k: [v for v in range(len(self.students))
                    if k in self.student_to_stop[v]]
                for k in range(1, len(self.stops))}
            self.clusters = Counter(
                [tuple(v) for k, v in self.student_to_stop.items()])
            self.stop_to_sc = {
                s: [c for c in self.clusters if s in c]
                for s in range(len(self.stops))}
            self.depots = eval(ls[3])
            self.capacity = eval(ls[4])
            self.g = eval(ls[5])


def distance_matrix(g, vset):
    dist = {}
    path = {}

    for vi in vset:
        dist[vi] = {v2: 2147483647 for v2 in g}
        path[vi] = {v2: [] for v2 in g}
        dist[vi][vi] = 0
        path[vi][vi] = [vi]
        seen = {v:False for v in g}
        h = [(0, vi)]
        while len(h) > 0:
            v = heappop(h)[1]
            if seen[v]:
                continue
            seen[v] = True
            for v2 in g[v]:
                nd = dist[vi][v] + g[v][v2][0]
                if nd < dist[vi][v2]:
                    path[vi][v2] = path[vi][v] + g[v][v2][1]
                    dist[vi][v2] = nd
                    heappush(h, (dist[vi][v2], v2))
        dist[vi] = {v: dist[vi][v] for v in dist[vi] if v in vset}
        path[vi] = {v: path[vi][v] for v in path[vi] if v in vset}
    return dist, path

def generate_students(n, stops, max_w):
    students = []
    for _ in range(n):
        st = choice(stops[1:])
        while True:
            std = (uniform(st[0] - max_w, st[0] + max_w),
                   uniform(st[1] - max_w, st[1] + max_w))
            if dist(std, st) <= max_w:
                break
        students.append(std)
    return students

def dist(x, y):
    return ((x[0] - y[0])**2 + (x[1] - y[1])**2)**.5


def print_solution(p):
    print("BEST OBJ: ", p.solution.get_objective_value())
    sol = p.solution.get_values()
    vnames = p.variables.get_names()
    dsol = {vnames[i]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}
    for k, v in dsol.items():
        print(k, v)

def process_solution(p):
    res = defaultdict(lambda: [])
    vnames = p.variables.get_names()
    vals = p.solution.get_values()
    dsol = {vnames[i]: vals[i] for i in range(len(vals))}
    for k,v in dsol.items():
        ks = k.split('_')
        if ks[0] == 'Edge' and v > 0.5:
            res[int(ks[1])].append(int(ks[2]))
    return res

def write_solution(p, filename):
    res = process_solution(p)
    with open(filename + '.out', 'w') as f:
        f.write(str(dict(res)) + '\n')

def plot_solution(data, p,filename = None):
    res = process_solution(p)
    plt.plot([data.stops[0][0]], [data.stops[0][1]], 'gs')
    plt.plot([data.stops[dep][0] for dep in data.depots],
            [data.stops[dep][1] for dep in data.depots], 'y^')
    plt.plot([data.stops[i][0] for i in range(1,len(data.stops)) if i not in data.depots],
            [data.stops[i][1] for i in range(1,len(data.stops)) if i not in data.depots], 'ro')
    plt.plot([s[0] for s in data.students], [s[1] for s in data.students], 'bx')
    
    res = process_solution(p)
    for v in res:
        for v2 in res[v]:
            plt.plot([data.stops[v][0], data.stops[v2][0]],
                     [data.stops[v][1], data.stops[v2][1]], 'b-')
    plt.show()

def old_product_constraints(res_vn, b_vn, n_vn, n_ub):
    rhs = [0, 0, -n_ub]
    sense = ['L', 'L', 'G']
    constraints = [
        [[res_vn, b_vn], [1, -n_ub]],
        [[res_vn, n_vn], [1, -1]],
        [[res_vn, n_vn, b_vn], [1, -1, -n_ub]]
    ]
    return (rhs, sense, constraints)


def kosaraju(graph):
    def visit(v):
        if not visited[v]:
            visited[v] = True
            for v2 in graph[v]:
                visit(v2)
            L.appendleft(v)
    
    def assign(v,root):
        if not assignment[v]:
            assignment[v] = root
            for v2 in tgraph[v]:
                assign(v2,root)


    tgraph = {v: [v2 for v2 in graph if v in graph[v2]] for v in graph}

    visited = {v:False for v in graph}
    assignment = {v:None for v in graph}
    L = deque([])
    for v in graph:
        visit(v)
    
    for v in L:
        assign(v,v)
    
    return assignment


def transpose(g):
    res = defaultdict(lambda:{})
    for v in g:
        for v2 in g[v]:
            res[v2][v] = g[v][v2]
    return res