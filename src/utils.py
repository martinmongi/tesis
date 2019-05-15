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
        with open(filename, 'r') as f:
            ls = f.readlines()
            self.original_graph = eval(ls[0])
            self.create_vdict()
            self.reverse_original_graph = transpose(self.original_graph)
            self.stops = eval(ls[1])
            self.school = self.stops[0]
            self.students = eval(ls[2])
            self.create_sdict()
            self.max_walk_dist = eval(ls[3])
            self.create_student_to_stop_dict()
            self.depots = eval(ls[4])
            self.capacity = eval(ls[5])

            self.distance, self.path = distance_matrix(
                self.original_graph, self.stops)

    def v_index(self, v):
        if v not in self.vdict:
            print("IMBECIL PEDISTE EL INDEX DE", v)
        else:
            return self.vdict[v]
    
    def s_index(self,s):
        return self.sdict[s]

    def create_vdict(self):
        self.vdict = {}
        self.vdictinv = []
        i = 0
        for v in self.original_graph:
            self.vdict[v] = i
            self.vdictinv.append(v) 
            i += 1

    def create_sdict(self):
        self.sdict = {self.students[i]: i
                 for i in range(len(self.students))}

    def create_student_to_stop_dict(self):
        self.student_to_stop = {s: {st: dist(st, s)
                                    for st in self.stops[1:]
                                    if dist(st, s) <= self.max_walk_dist}
                                for s in self.students}

    def add_solution(self, stop_assignment, routes):
        self.routes = routes
        self.stop_assignment = stop_assignment
    
    def write_solution(self, filename):
        with open(filename, 'w') as f:
            for v0 in self.routes:
                f.write(str(dict(self.routes[v0])) + '\n')
            f.write(str(dict(self.stop_assignment)))






def bfs(g, v0):
        seen = set([v0])
        q = deque([v0])
        while len(q) > 0:
            v = q.popleft()
            seen.add(v)
            for v2 in g[v]:
                if v2 not in seen:
                    q.append(v2)
        return seen

def vn(*argv):
    return "_".join(map(str, argv))

def distance_matrix(g, vset):
    dist = {}
    path = {}
    for vi in vset:
        dist[vi] = {}
        path[vi] = {}
        seen = {v: False for v in g}
        h = [(0.0, vi, [vi])]
        while len(h) > 0:
            v = heappop(h)
            if seen[v[1]]:
                continue
            seen[v[1]] = True
            dist[vi][v[1]] = v[0]
            path[vi][v[1]] = v[2]
            for v2 in g[v[1]]:
                heappush(h, (v[0] + g[v[1]][v2][0],v2, v[2] + [v2]))
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

    def assign(v, root):
        if not assignment[v]:
            assignment[v] = root
            for v2 in tgraph[v]:
                assign(v2, root)

    tgraph = {v: [v2 for v2 in graph if v in graph[v2]] for v in graph}
    visited = {v: False for v in graph}
    assignment = {v: None for v in graph}
    L = deque([])
    for v in graph:
        visit(v)
    for v in L:
        assign(v, v)
    return assignment


def transpose(g):
    res = defaultdict(lambda: {})
    for v in g:
        for v2 in g[v]:
            res[v2][v] = g[v][v2]
    return res
