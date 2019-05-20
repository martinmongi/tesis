from math import fabs
from collections import defaultdict, Counter, deque
from random import choice, uniform
from itertools import combinations_with_replacement
import matplotlib.pyplot as plt
from heapq import heappop, heappush
import sys
from pprint import pprint
import copy


class ProblemData:
    def __init__(self, filename):
        with open(filename, 'r') as f:
            ls = f.readlines()
            self.original_graph = eval(ls[0])
            print("LEYENDO MODELO CON", len(self.original_graph), "ESQUINAS")
            print("                  ",
                  sum(len(self.original_graph[v])
                      for v in self.original_graph), "CUADRAS")
            self.reverse_original_graph = transpose(self.original_graph)
            self.create_vdict()
            self.stops = eval(ls[1])
            print("                  ", len(self.stops), "PARADAS")
            self.school = self.stops[0]
            self.students = eval(ls[2])
            print("                  ", len(self.students), "ESTUDIANTES")
            self.create_sdict()
            self.max_walk_dist = eval(ls[3])
            self.create_student_to_stop_dict()
            self.depots = eval(ls[4])
            self.capacity = eval(ls[5])
            print("                  ", len(self.depots),
                  "BUSES DE CAPACIDAD", self.capacity)
            self.create_distance_matrix()
            self.create_direct_edge_dict()
            self.create_max_flow_dict()

    def create_max_flow_dict(self):
        self.edge_max_flow = {}
        for e, tours in self.direct_edge_dict.items():
            V1 = set([("START", i) for i, j in tours])
            V2 = set([("END", j) for i, j in tours])
            extras = set([("SOURCE"), ("SINK")])
            V = V1.union(V2).union(extras)
            g = {vi: defaultdict(lambda: 0) for vi in V}
            for i, j in tours:
                g[("SOURCE")][("START", i)] = 1
                g[("START", i)][("END", j)] = 1
                if j == self.school:
                    g[("END", j)][("SINK")] += 1
                else:
                    g[("END", j)][("SINK")] = 1
            if ("END", self.school) in V:
                g[("END", self.school)][("SINK")] = min(
                    g[("END", self.school)][("SINK")], len(self.depots))
            self.edge_max_flow[e] = max_flow(g, "SOURCE", "SINK")

    def create_direct_edge_dict(self):
        self.direct_edge_dict = {(i, j): [] for i in self.original_graph
                                 for j in self.original_graph[i]}
        for v1 in self.path:
            for v2 in self.path[v1]:
                p = self.path[v1][v2]
                # print(len(p))
                for i in range(len(p) - 1):
                    self.direct_edge_dict[(p[i], p[i + 1])].append((v1, v2))
        # for e in self.direct_edge_dict:
            # print(e, len(set([i for i, j in self.direct_edge_dict[e]])),
            #     len(set([j for i, j in self.direct_edge_dict[e]])))

    def create_distance_matrix(self):
        g = self.original_graph
        vset = self.stops
        self.dist = {}
        self.path = {}
        for vi in vset:
            self.dist[vi] = {}
            self.path[vi] = {}
            seen = {v: False for v in g}
            h = [(0.0, vi, [vi])]
            while len(h) > 0:
                v = heappop(h)
                if seen[v[1]]:
                    continue
                seen[v[1]] = True
                self.dist[vi][v[1]] = v[0]
                self.path[vi][v[1]] = v[2]
                for v2 in g[v[1]]:
                    heappush(h, (v[0] + g[v[1]][v2][0], v2, v[2] + [v2]))
            self.dist[vi] = {v: self.dist[vi][v]
                             for v in self.dist[vi] if v in vset}
            self.path[vi] = {v: self.path[vi][v]
                             for v in self.path[vi] if v in vset}

    def v_index(self, v):
        if v not in self.vdict:
            print("IMBECIL PEDISTE EL INDEX DE", v)
        else:
            return self.vdict[v]

    def s_index(self, s):
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


def max_flow(graph, source, sink):
    def flow_bfs(g, s, t, rc):
        visited = {i: False for i in rc}
        prev = {i: None for i in rc}
        q = deque([s])
        while len(q) > 0:
            v = q.popleft()
            # print(v)
            visited[v] = True
            for v2 in rc[v]:
                if (not visited[v2]):
                    # print(v,"->",v2)
                    q.append(v2)
                    prev[v2] = v

        # print(prev)
        if prev[t] == None:
            return None
        v = t
        path = []
        while prev[v] != None:
            # print(v, prev[v])
            path.append(v)
            v = prev[v]
            # print(v, prev[v])
        path.append(s)
        path.reverse()
        return path

    rc = copy.deepcopy(graph)
    flow = 0
    while True:
        path = flow_bfs(graph, source, sink, rc)
        # print("Path:",path)
        if not path:
            return flow
        flow += 1
        for i in range(0, len(path) - 1):
            del rc[path[i]][path[i + 1]]
            rc[path[i + 1]][path[i]] = 1
    return flow


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
