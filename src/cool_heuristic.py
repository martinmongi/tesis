from pprint import pprint
from copy import deepcopy
from utils import vn
import cplex
import heapq
from student_assignment import assign_students_mip
from collections import defaultdict


class CoolHeuristic:
    def __init__(self, data):
        self.data = data
        self.feasibility = {}
        self.construct()
        self.descend()
        # self.pp()

    def pp(self):
        pprint({self.data.v_index(v0): list(
            map(self.data.v_index, self.paths[v0])) for v0 in self.paths})

    def feasible(self, paths, wont_be_routed):
        tpaths = tuple(sorted([tuple(sorted(p)) for v0,p in paths.items()]))
        tunrouted = tuple(sorted(wont_be_routed))
        if (tpaths,tunrouted) in self.feasibility:
            return self.feasibility[(tpaths,tunrouted)]
        self.feasibility[(tpaths, tunrouted)] = self.feasible_aux(
            paths, wont_be_routed)
        return self.feasibility[(tpaths, tunrouted)]

    def feasible_aux(self,paths,wont_be_routed):
        problem = cplex.Cplex()
        problem.parameters.emphasis.mip.set(1)
        problem.parameters.mip.display.set(0)
        problem.set_log_stream(None)
        problem.set_error_stream(None)
        problem.set_warning_stream(None)
        problem.set_results_stream(None)

        variables = [(vn('RouteStop', self.data.v_index(v0), self.data.v_index(v1)), 'B', 0)
                     for v0 in paths for v1 in self.data.stops[1:]] + \
            [(vn('RouteStopCluster', self.data.v_index(v0), self.data.v_index(v1), list(map(self.data.v_index, c))), 'I', 1)
             for v0 in paths for v1 in self.data.stops for c in self.data.stop_to_clusters[v1]]

        problem.variables.add(types=[v[1] for v in variables],
                              names=[v[0] for v in variables])

        # All stops can be visited at most one time
        rhs = [1 for v in self.data.stops[1:]]
        sense = ['L' for v in self.data.stops[1:]]
        constraint = [[
            [vn('RouteStop', self.data.v_index(v0), self.data.v_index(v))
                for v0 in paths],
            [1 for v0 in paths]
        ] for v in self.data.stops[1:]]
        problem.linear_constraints.add(
            lin_expr=constraint, senses=sense, rhs=rhs)

        # Cluster choices add to cluster size
        rhs = [self.data.clusters[c] for c in self.data.clusters]
        sense = ['E' for c in self.data.clusters]
        constraint = [[
            [vn('RouteStopCluster', self.data.v_index(v0), self.data.v_index(
                v1), list(map(self.data.v_index, c))) for v0 in paths for v1 in c],
            [1 for v0 in paths for v1 in c]
        ] for c in self.data.clusters]
        problem.linear_constraints.add(
            lin_expr=constraint, senses=sense, rhs=rhs)

        # If cluster to stop, route is larger than 1, stop,route must be active
        rhs = [
            0 for v0 in paths for v1 in self.data.stops for c in self.data.stop_to_clusters[v1]]
        sense = [
            'L' for v0 in paths for v1 in self.data.stops for c in self.data.stop_to_clusters[v1]]
        constraint = [[
            [vn('RouteStopCluster', self.data.v_index(v0), self.data.v_index(v1), list(map(self.data.v_index, c))),
             vn('RouteStop', self.data.v_index(v0), self.data.v_index(v1))],
            [1, - self.data.clusters[c]]
        ] for v0 in paths for v1 in self.data.stops for c in self.data.stop_to_clusters[v1]]
        problem.linear_constraints.add(
            lin_expr=constraint, senses=sense, rhs=rhs)

        # Capacities are kept
        rhs = [self.data.capacity for v0 in paths]
        sense = ['L' for v0 in paths]
        constraint = [[
            [vn('RouteStopCluster', self.data.v_index(v0), self.data.v_index(v1), list(map(self.data.v_index, c)))
             for v1 in self.data.stops for c in self.data.stop_to_clusters[v1]],
            [1 for v1 in self.data.stops for c in self.data.stop_to_clusters[v1]]
        ] for v0 in paths]
        problem.linear_constraints.add(
            lin_expr=constraint, senses=sense, rhs=rhs)

        rhs = []
        sense = []
        constraint = []
        for v0 in paths:
            for v in paths[v0][:-1]:
                rhs.append(1)
                sense.append('E')
                constraint.append(
                    [[vn('RouteStop', self.data.v_index(v0), self.data.v_index(v))],
                     [1]])
        for v in wont_be_routed:
            rhs.append(0)
            sense.append('E')
            constraint.append(
                [[vn('RouteStop', self.data.v_index(v0), self.data.v_index(v)) for v0 in paths],
                    [1 for v0 in paths]])
        problem.linear_constraints.add(
            lin_expr=constraint, senses=sense, rhs=rhs)

        problem.solve()
        return problem.solution.is_primal_feasible()

    def construct(self):
        self.paths = {d: [d, self.data.school] for d in self.data.depots}
        self.unrouted = self.data.stops[:]
        for v in (self.data.depots + [self.data.school]):
            self.unrouted.remove(v)
        if not self.feasible(self.paths, []):
            return False

        cant_add = set()
        while len(self.unrouted) > 0:
            if len(self.unrouted) % 10 == 0:
                print("Heuristic constructing,", len(
                    self.unrouted), "vertices remaining")
            savings = []
            for v in self.unrouted:
                for v0 in self.paths:
                    for i in range(len(self.paths[v0]) - 1):
                        vi = self.paths[v0][i]
                        vj = self.paths[v0][i + 1]
                        savings.append(
                            (self.data.dist[vi][v] + self.data.dist[v][vj] - self.data.dist[vi][vj],
                             v, v0, i))

            heapq.heapify(savings)
            while len(savings) > 0:
                _, v, v0, i = heapq.heappop(savings)
                new_paths = deepcopy(self.paths)
                new_paths[v0] = new_paths[v0][:i + 1] + \
                    [v] + new_paths[v0][i + 1:]
                if (v, v0) not in cant_add and self.feasible(new_paths, []):
                    self.paths = new_paths
                    self.unrouted.remove(v)
                    break
                else:
                    cant_add.add((v, v0))

    def descend(self):
        improved = True
        while True:
            # self.pp()
            savings = []
            savings += self.removal_savings()
            savings += self.rem_ins_within_savings()
            savings += self.rem_ins_between_savings()
            savings += self.replace_savings()
            savings += self.merge_savings()
            savings.sort()
            if not improved:
                break

            improved = False
            for s, com, t in savings:
                # print(s,com,t)
                if com == 'remove':
                    v0, i = t
                    np = remove(self.paths, t)
                    if self.feasible(np, self.unrouted + [self.paths[v0][i]]):
                        print("Removing vertex", self.data.v_index(
                            self.paths[v0][i]), "in route", self.data.v_index(v0), "saving", round(-s, 2))
                        # print(s, com, self.data.v_index(v0), i)
                        self.unrouted.append(self.paths[v0][i])
                        # print(list(map(self.data.v_index, self.unrouted)))
                        self.paths = np
                        # print(com,t)
                        # pprint(self.paths)
                        improved = True
                        break
                elif com == 'rem_ins_within':
                    v0, i, j = t
                    np = rem_ins_within(self.paths, t)
                    print("Moving vertex", self.data.v_index(
                        self.paths[v0][i]), "in route", self.data.v_index(v0), "saving", round(-s, 2))
                    # print(s, com, self.data.v_index(v0), i, j)
                    # print(list(map(self.data.v_index, self.unrouted)))
                    self.paths = np
                    # print(com,t)
                    # pprint(self.paths)
                    improved = True
                    break
                elif com == 'rem_ins_between':
                    v0, i, u0, j = t
                    np = rem_ins_between(self.paths, t)
                    if self.feasible(np, self.unrouted):
                        # print(s, com, self.data.v_index(v0),
                        #       i, self.data.v_index(u0), j)
                        print("Moving vertex", self.data.v_index(
                            self.paths[v0][i]), "in route", self.data.v_index(v0),
                            "to route",  self.data.v_index(u0), "saving", round(-s, 2))
                        # print(list(map(self.data.v_index, self.unrouted)))
                        self.paths = np
                        # print(com,t)
                        # pprint(self.paths)
                        improved = True
                        break
                elif com == 'replace':
                    v0, i, v_in = t
                    np = replace(self.paths, t)
                    nur = deepcopy(self.unrouted)
                    nur.append(self.paths[v0][i])
                    nur.remove(v_in)
                    if self.feasible(np, nur):
                        # print(s, com, self.data.v_index(v0),
                        #       i, self.data.v_index(v_in))
                        print("Replacing vertex", self.data.v_index(
                            self.paths[v0][i]), "in route", self.data.v_index(v0),
                            "with",  self.data.v_index(v_in), "saving", round(-s, 2))
                        self.paths = np
                        self.unrouted = nur
                        # print(list(map(self.data.v_index, self.unrouted)))
                        # print(com,t)
                        # pprint(self.paths)
                        improved = True
                        break
                elif com == 'merge':
                    v0, u0 = t
                    np = merge(self.paths, t)
                    if self.feasible(np, self.unrouted):
                        # print(s, com, self.data.v_index(
                        #     v0), self.data.v_index(u0))
                        print("Merging routes", self.data.v_index(v0),
                              "and ", self.data.v_index(u0), "saving", round(-s, 2))
                        # print(list(map(self.data.v_index, self.unrouted)))
                        self.paths = np
                        improved = True
                        break

    def removal_savings(self):
        savings = []
        for v0 in self.paths:
            for i in range(1, len(self.paths[v0]) - 1):
                v_prev = self.paths[v0][i - 1]
                v = self.paths[v0][i]
                v_next = self.paths[v0][i + 1]
                sv = self.data.dist[v_prev][v_next] - \
                    self.data.dist[v_prev][v] - self.data.dist[v][v_next]
                if sv < -0.1:
                    savings.append((sv, 'remove', (v0, i)))
                # ns = rem(self.paths, (v0,i))
                # print(sv, v0, v, self.feasible(ns,[v]), sep='\t')
        return savings

    def rem_ins_within_savings(self):
        savings = []
        for v0 in self.paths:
            p = self.paths[v0]
            for i in range(1, len(p) - 1):
                v_prev = p[i - 1]
                v = p[i]
                v_next = p[i + 1]
                sv_rem = self.data.dist[v_prev][v_next] - \
                    self.data.dist[v_prev][v] - self.data.dist[v][v_next]

                for j in range(1, len(p) - 1):
                    if i < j:
                        u_prev = p[j]
                        u_next = p[j + 1]
                    elif i == j:
                        continue
                    else:
                        u_prev = p[j - 1]
                        u_next = p[j]
                    sv_ins = - self.data.dist[u_prev][u_next] + \
                        self.data.dist[u_prev][v] + self.data.dist[v][u_next]
                    if sv_ins + sv_rem < -0.1:
                        savings.append(
                            (sv_ins + sv_rem, 'rem_ins_within', (v0, i, j)))
                    # ns = rem_ins_within(self.paths,(v0,i,j))
                    # print(sv_ins + sv_rem, i, j, self.feasible(ns,[]), sep='\t')
        return savings

    def rem_ins_between_savings(self):
        savings = []
        for v0 in self.paths:
            p1 = self.paths[v0]
            for u0 in self.paths:
                if v0 == u0:
                    continue
                p2 = self.paths[u0]

                for i in range(1, len(p1) - 1):
                    v_prev = p1[i - 1]
                    v = p1[i]
                    v_next = p1[i + 1]
                    sv_rem = self.data.dist[v_prev][v_next] - \
                        self.data.dist[v_prev][v] - self.data.dist[v][v_next]

                    for j in range(1, len(p2)):
                        u_prev = p2[j - 1]
                        u_next = p2[j]
                        sv_ins = - self.data.dist[u_prev][u_next] + \
                            self.data.dist[u_prev][v] + \
                            self.data.dist[v][u_next]
                        if sv_ins + sv_rem < -0.1:
                            savings.append(
                                (sv_ins + sv_rem, 'rem_ins_between', (v0, i, u0, j)))
                        # ns = rem_ins_between(self.paths, (v0, i, u0, j))
                        # print(sv_ins + sv_rem, i, j,
                        #     self.feasible(ns, []), sep='\t')
        return savings

    def replace_savings(self):
        savings = []
        for v0 in self.paths:
            p = self.paths[v0]
            for i in range(1, len(p) - 1):
                v_prev = p[i - 1]
                v_out = p[i]
                v_next = p[i + 1]
                for v_in in self.unrouted:
                    sv = - self.data.dist[v_prev][v_out] - \
                        self.data.dist[v_out][v_next] + self.data.dist[v_prev][v_in] + \
                        self.data.dist[v_in][v_next]
                    if sv < -0.1:
                        savings.append((sv, 'replace', (v0, i, v_in)))
        return savings

    # Probably should merge better
    def merge_savings(self):
        savings = []
        for v0 in self.paths:
            p1 = self.paths[v0]
            for u0 in self.paths:
                if u0 == v0:
                    continue
                v_last = p1[-2]
                sv = -self.data.dist[v_last][self.data.school] + \
                    self.data.dist[v_last][u0]
                if sv < -0.1:
                    savings.append((sv, 'merge', (v0, u0)))
                    # print(v0,u0,sv)
        return savings

    def precalc_varset(self, varset, grouped=False):
        # pprint(varset)
        vs = {v: 0 for v in varset}
        self.graphs = {v0: {self.paths[v0][i]: {self.paths[v0][i + 1]: None}
                            for i in range(len(self.paths[v0]) - 1)} for v0 in self.paths}
        stop_to_route = {}

        for v0 in self.graphs:
            vs[vn('RouteActive', self.data.v_index(v0))] = 1
            for v in self.graphs[v0]:
                vs[vn('RouteStop', self.data.v_index(
                    v0), self.data.v_index(v))] = 1
                stop_to_route[v] = v0
                for v2 in self.graphs[v0][v]:
                    vs[vn('RouteEdge', self.data.v_index(v0), self.data.v_index(
                        v), self.data.v_index(v2))] = 1

        assignment = assign_students_mip(self.data, self.graphs)
        for s in assignment:
            v = assignment[s]
            c = self.data.student_to_stop[s]
            v0 = stop_to_route[v]
            if grouped:
                vs[vn('RouteStopCluster', self.data.v_index(v0),
                      self.data.v_index(v), sorted(list(map(self.data.v_index, c))))] += 1
            else:
                vs[vn('RouteStopStudent', self.data.v_index(v0),
                      self.data.v_index(v), self.data.s_index(s))] = 1
        # pprint(vs)
        res = [varset, [vs[v] for v in varset]]
        # exit()
        return res

    def direct_varset(self, varset, grouped=False):
        # pprint(varset)
        vs = {v: 0 for v in varset}
        self.graphs = {v0: {self.paths[v0][i]: {self.paths[v0][i + 1]: None}
                            for i in range(len(self.paths[v0]) - 1)} for v0 in self.paths}
        stop_to_route = {}

        for v0 in self.graphs:
            vs[vn('RouteActive', self.data.v_index(v0))] = 1
            for v in self.graphs[v0]:
                vs[vn('RouteStop', self.data.v_index(
                    v0), self.data.v_index(v))] = 1
                stop_to_route[v] = v0
                for v2 in self.graphs[v0][v]:
                    smallpath = self.data.path[v][v2]
                    for j in range(len(smallpath) - 1):
                        vs[vn('RouteEdge', self.data.v_index(v0),
                              self.data.v_index(smallpath[j]),
                              self.data.v_index(smallpath[j + 1]))] += 1

        assignment = assign_students_mip(self.data, self.graphs)
        for s in assignment:
            v = assignment[s]
            c = self.data.student_to_stop[s]
            v0 = stop_to_route[v]
            if grouped:
                vs[vn('RouteStopCluster', self.data.v_index(v0),
                      self.data.v_index(v), sorted(list(map(self.data.v_index, c))))] += 1
            else:
                vs[vn('RouteStopStudent', self.data.v_index(v0),
                      self.data.v_index(v), self.data.s_index(s))] = 1
        # pprint(vs)
        res = [varset, [vs[v] for v in varset]]
        # exit()
        return res

    def flat_varset(self, varset, grouped=False):
            # pprint(varset)
        vs = {v: 0 for v in varset}
        self.graphs = {v0: {self.paths[v0][i]: {self.paths[v0][i + 1]: None}
                            for i in range(len(self.paths[v0]) - 1)} for v0 in self.paths}
        stop_to_route = {}

        for v0 in self.graphs:
            vs[vn('RouteActive', self.data.v_index(v0))] = 1
            for v in self.graphs[v0]:
                vs[vn('Stop', self.data.v_index(v))] = 1
                stop_to_route[v] = v0
                for v2 in self.graphs[v0][v]:
                    vs[vn('Edge', self.data.v_index(v), self.data.v_index(v2))] = 1

        assignment = assign_students_mip(self.data, self.graphs)
        for s in assignment:
            v = assignment[s]
            c = self.data.student_to_stop[s]
            v0 = stop_to_route[v]
            if grouped:
                vs[vn('StopCluster', self.data.v_index(v),
                      sorted(list(map(self.data.v_index, c))))] += 1
            else:
                vs[vn('StopStudent', self.data.v_index(
                    v), self.data.s_index(s))] = 1
            vs[vn('StopLoad', self.data.v_index(v))] += 1

        for v0 in self.paths:
            for i in range(1, len(self.paths[v0])):
                v1 = self.paths[v0][i - 1]
                v2 = self.paths[v0][i]
                vs[vn('EdgeLoad', self.data.v_index(v1), self.data.v_index(v2))
                   ] = vs[vn('StopLoad', self.data.v_index(v1))]
                vs[vn('StopLoad', self.data.v_index(v2))
                   ] += vs[vn('StopLoad', self.data.v_index(v1))]
        # pprint(vs)
        res = [varset, [vs[v] for v in varset]]
        # exit()
        return res


def remove(paths, t):
    v0, i = t
    res = deepcopy(paths)
    res[v0] = res[v0][:i] + res[v0][i + 1:]
    return res


def rem_ins_within(paths, t):
    v0, i, j = t
    res = deepcopy(paths)
    v = res[v0][i]
    res[v0] = res[v0][:i] + res[v0][i + 1:]
    res[v0] = res[v0][:j] + [v] + res[v0][j:]
    return res


def rem_ins_between(paths, t):
    v0, i, u0, j = t
    res = deepcopy(paths)
    v = res[v0][i]
    res[v0] = res[v0][:i] + res[v0][i + 1:]
    res[u0] = res[u0][:j] + [v] + res[u0][j:]
    return res


def replace(paths, t):
    v0, i, v_in = t
    res = deepcopy(paths)
    res[v0][i] = v_in
    return res


def merge(paths, t):
    v0, u0 = t
    res = deepcopy(paths)
    res[v0] = res[v0][:-1] + res[u0]
    del res[u0]
    return res
