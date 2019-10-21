import re
from collections import Counter, defaultdict, deque
from pprint import pprint
from sys import argv
from optparse import OptionParser
from student_assignment import assign_students_mip
from random import shuffle
from union_find import UnionFind
from cool_heuristic import CoolHeuristic

import cplex

from utils import (ProblemData, bfs, dist, old_product_constraints, transpose,
                   vn)

parser = OptionParser()
parser.add_option("--if", dest="in_file")
parser.add_option("--of", dest="out_file")
parser.add_option("--mtz", dest="mtz", action="store_true")
parser.add_option("--dfj", dest="mtz", action="store_false")
parser.add_option("--grouped", dest="grouped", action="store_true")
parser.add_option("--heur", dest="heur", action="store_true")
parser.add_option("--nodeheur", dest="node_heur", action="store_true")

(options, args) = parser.parse_args()

# INPUT
data = ProblemData(options.in_file)

problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)
# problem.parameters.dettimelimit.set(1000000)
problem.parameters.timelimit.set(3600)
problem.parameters.workmem.set(20000)


variables = [
    (vn('RoEd', data.v_index(v0), data.v_index(
        v1), data.v_index(v2)), 'B', data.dist[v1][v2])
    for v0 in data.depots for v1 in data.stops for v2 in data.stops if v1 != v2] + \
    [(vn('RoSto', data.v_index(v0), data.v_index(v1)), 'B', 0)
     for v0 in data.depots for v1 in data.stops[1:]] + \
    [(vn('RoA', data.v_index(v0)), 'B', 0) for v0 in data.depots]

if True:
    variables += [(vn('RoStoCl', data.v_index(v0), data.v_index(v1), sorted(list(map(data.v_index, c)))), 'I', 0)
                  for v0 in data.depots for v1 in data.stops for c in data.stop_to_clusters[v1]]
else:
    variables += [(vn('RoStoStu', data.v_index(v0), data.v_index(v1), data.s_index(s)), 'B', 0)
                  for s in data.students for v0 in data.depots for v1 in data.student_to_stop[s]]

if True:
    variables += [(vn('Rank', data.v_index(v0), data.v_index(v)), 'C', 0)
                  for v0 in data.depots for v in data.stops]

problem.variables.add(obj=[v[2] for v in variables],
                      types=[v[1] for v in variables],
                      names=[v[0] for v in variables])

# All vertices have equal in and out degree, other than depots on their own tour
# or school in all depots
rhs = [0 for v0 in data.depots for v in data.stops
       if v not in [data.school, v0]]
sense = ['E' for v0 in data.depots for v in data.stops
         if v not in [data.school, v0]]
constraint = [[
    [vn('RoEd', data.v_index(v0), data.v_index(v), data.v_index(v2))
     for v2 in data.stops if v != v2] +
    [vn('RoEd', data.v_index(v0), data.v_index(v2), data.v_index(v))
     for v2 in data.stops if v != v2],
    [1 for v2 in data.stops if v != v2] +
    [-1 for v2 in data.stops if v != v2]
] for v0 in data.depots for v in data.stops if v not in [data.school, v0]]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# All outdegs constrained by 1
rhs = [1 for v in data.stops]
sense = ['L' for v in data.stops]
constraint = [[
    [vn('RoEd', data.v_index(v0), data.v_index(v), data.v_index(v2))
     for v0 in data.depots for v2 in data.stops if v != v2],
    [1 for v0 in data.depots for v2 in data.stops if v != v2]
] for v in data.stops]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# outdeg - indeg = RoA
# All depots have 0 <= outdeg - indeg <= 1 in their own tours (constrainted by binarity of RoA)
rhs = [0] * len(data.depots)
sense = ['E'] * len(data.depots)
constraint = [[
    [vn('RoEd', data.v_index(v0), data.v_index(v0), data.v_index(v2))
     for v2 in data.stops if v2 != v0] +
    [vn('RoEd', data.v_index(v0), data.v_index(v2), data.v_index(v0))
     for v2 in data.stops if v2 != v0] +
    [vn('RoA', data.v_index(v0))],
    [1 for v2 in data.stops if v2 != v0] +
    [-1 for v2 in data.stops if v2 != v0] +
    [-1]
] for v0 in data.depots]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# outdeg - indeg = - RoA
# School has -1 <= outdeg - indeg <= 0 for all tours (constrained by binarity of RoA)
rhs = [0] * len(data.depots)
sense = ['E'] * len(data.depots)
constraint = [[
    [vn('RoEd', data.v_index(v0), data.v_index(data.school), data.v_index(v2))
     for v2 in data.stops if v2 != data.school] +
    [vn('RoEd', data.v_index(v0), data.v_index(v2), data.v_index(data.school))
     for v2 in data.stops if v2 != data.school] +
    [vn('RoA', data.v_index(v0))],
    [1 for v2 in data.stops if v2 != data.school] +
    [-1 for v2 in data.stops if v2 != data.school] +
    [1]
] for v0 in data.depots]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# Having out degree means vertex in stops can have stop
rhs = [0 for v0 in data.depots for v in data.stops[1:]]
sense = ['E' for v0 in data.depots for v in data.stops[1:]]
constraint = [[
    [vn('RoEd', data.v_index(v0), data.v_index(v), data.v_index(v2))
     for v2 in data.stops if v2 != v] +
    [vn('RoSto', data.v_index(v0), data.v_index(v))],
    [1 for v2 in data.stops if v2 != v] + [-1]
] for v0 in data.depots for v in data.stops[1:]]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# All stops can be visited at most one time
rhs = [1 for v in data.stops[1:]]
sense = ['L' for v in data.stops[1:]]
constraint = [[
    [vn('RoSto', data.v_index(v0), data.v_index(v)) for v0 in data.depots],
    [1 for v0 in data.depots]
] for v in data.stops[1:]]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

if True:
    # Cluster choices add to cluster size
    rhs = [data.clusters[c] for c in data.clusters]
    sense = ['E' for c in data.clusters]
    constraint = [[
        [vn('RoStoCl', data.v_index(v0), data.v_index(
            v1), sorted(list(map(data.v_index, c)))) for v0 in data.depots for v1 in c],
        [1 for v0 in data.depots for v1 in c]
    ] for c in data.clusters]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # If cluster to stop, route is larger than 1, stop,route must be active
    rhs = [0 for v0 in data.depots for v1 in data.stops for c in data.stop_to_clusters[v1]]
    sense = [
        'L' for v0 in data.depots for v1 in data.stops for c in data.stop_to_clusters[v1]]
    constraint = [[
        [vn('RoStoCl', data.v_index(v0), data.v_index(v1), sorted(list(map(data.v_index, c)))),
         vn('RoSto', data.v_index(v0), data.v_index(v1))],
        [1, - data.clusters[c]]
    ] for v0 in data.depots for v1 in data.stops for c in data.stop_to_clusters[v1]]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # Capacities are kept
    rhs = [data.capacity for v0 in data.depots]
    sense = ['L' for v0 in data.depots]
    constraint = [[
        [vn('RoStoCl', data.v_index(v0), data.v_index(v1), sorted(list(map(data.v_index, c))))
         for v1 in data.stops for c in data.stop_to_clusters[v1]],
        [1 for v1 in data.stops for c in data.stop_to_clusters[v1]]
    ] for v0 in data.depots]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)
else:
    # Stop choices for each student add to 1
    rhs = [1 for s in data.students]
    sense = ['E' for s in data.students]
    constraint = [[
        [vn('RoStoStu', data.v_index(v0), data.v_index(v1), data.s_index(s))
         for v0 in data.depots for v1 in data.student_to_stop[s]],
        [1 for v0 in data.depots for v1 in data.student_to_stop[s]],
    ] for s in data.students]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # If student chooses stop, it must be in a tour
    rhs = [0 for s in data.students for v0 in data.depots for v in data.student_to_stop[s]]
    sense = [
        'L' for s in data.students for v0 in data.depots for v in data.student_to_stop[s]]
    constraint = [[
        [vn('RoStoStu', data.v_index(v0), data.v_index(v), data.s_index(s)),
         vn('RoSto', data.v_index(v0), data.v_index(v))],
        [1, -1]
    ] for s in data.students for v0 in data.depots for v in data.student_to_stop[s]]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # Capacities are kept
    rhs = [data.capacity for v0 in data.depots]
    sense = ['L' for v0 in data.depots]
    constraint = [[
        [vn('RoStoStu', data.v_index(v0), data.v_index(v), data.s_index(s))
         for s in data.students for v in data.student_to_stop[s]],
        [1 for s in data.students for v in data.student_to_stop[s]]
    ] for v0 in data.depots]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# If a stop is on, the route should be active
rhs = [0 for v in data.stops[1:] for v0 in data.depots]
sense = ['G' for v in data.stops[1:] for v0 in data.depots]
constraint = [[
    [vn('RoSto', data.v_index(v0), data.v_index(v)),
     vn('RoA', data.v_index(v0))],
    [-1, 1]
] for v in data.stops[1:] for v0 in data.depots]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

if True:
    for v0 in data.depots:
        # Depots have rank 1
        rhs = [1]
        sense = ['E']
        constraint = [[[vn('Rank', data.v_index(v0), data.v_index(v0))], [1]]]
        problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                                       names=[vn('irank', data.v_index(v0))])

        # Routes keep rank
        M = len(data.stops)
        gen = [(i, j) for i in data.stops for j in data.stops
               if i != j and i != v0 and j != data.school]
        rhs = [1 - M for i, j in gen]
        sense = ['G' for i, j in gen]
        constraint = [[
            [vn('Rank', data.v_index(v0), data.v_index(j)),
             vn('Rank', data.v_index(v0), data.v_index(i)),
             vn('RoEd', data.v_index(v0), data.v_index(i), data.v_index(j))],
            [1, -1, -M]
        ] for i, j in gen]
        problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                                       names=[vn('crank', data.v_index(v0),
                                                 data.v_index(i), data.v_index(j)) for i, j in gen])
else:
    class SubToursLazyConstraintCallback(cplex.callbacks.LazyConstraintCallback):
        def __call__(self):
            sols = self.get_values()
            dsol = {variables[i][0]: sols[i]
                    for i in range(len(sols)) if sols[i] > 0.5}
            gs = {data.v_index(v0): defaultdict(lambda: [])
                  for v0 in data.depots}
            for vname in dsol:
                sp = vname.split("_")
                if sp[0] == 'RoEd':
                    v0, i, j = map(int, sp[1:])
                    gs[v0][i].append(j)

            for v0, g in gs.items():
                main_tour = bfs(g, v0)
                loops = set([v for v in g]).difference(main_tour)
                while len(loops) > 0:
                    loop = bfs(g, loops.pop())
                    for v00 in data.depots:
                        rhs = len(loop) - 1
                        sense = 'L'
                        constraint = [
                            [vn('RoEd', data.v_index(v00), v1, v2)
                             for v1 in loop for v2 in loop if v1 != v2],
                            [1 for v1 in loop for v2 in loop if v1 != v2]
                        ]
                        self.add(constraint=constraint,
                                 sense=sense,
                                 rhs=rhs)
                    loops.difference_update(loop)
    problem.register_callback(SubToursLazyConstraintCallback)

if options.node_heur:
    class NodeHeuristicCallback(cplex.callbacks.HeuristicCallback):
        def __call__(self):

            # Generamos diccionarios para obtener rapidamente las variables
            val_dict = {x[0][0]: x[1]
                        for x in zip(variables, self.get_values())}
            # pprint(val_dict)
            stop_route = defaultdict(lambda: [])
            student_stop_route = defaultdict(lambda: [])
            edges_cost = defaultdict(lambda: defaultdict(lambda: {}))
            for vname in val_dict:
                sp = vname.split("_")
                if sp[0] == 'RoSto':
                    v0, s = map(int, sp[1:])
                    stop_route[s].append((val_dict[vname], v0))
                if sp[0] == 'RoStoStu':
                    v0, s, st = map(int, sp[1:])
                    student_stop_route[st].append((val_dict[vname], v0, s))
                if sp[0] == 'RoEd':
                    v0, s1, s2 = map(int, sp[1:])
                    edges_cost[v0][s1][s2] = (1 - val_dict[vname]) * \
                        data.dist[data.vdictinv[s1]][data.vdictinv[s2]]

            # Shuffleando para no tener sesgo hacia ciertas paradas/estudiantes
            for s in stop_route:
                shuffle(stop_route[s])
            for st in student_stop_route:
                shuffle(student_stop_route[st])
            # pprint(stop_route)
            # pprint(student_stop_route)

            rvars = defaultdict(lambda: 0)
            stop_route_choice = {}
            routes = defaultdict(lambda: {})
            # De cada parada, elegimos la ruta que tenga mayor de asociación entre
            # ruta y parada. Si todas son 0, entonces la dejamos afuera. Al mismo
            # tiempo, activamos las rutas
            for s in stop_route:
                highest = 0.0
                best = None
                for val, v0 in stop_route[s]:
                    if val > highest:
                        highest = val
                        best = v0
                stop_route_choice[s] = best
                if best is not None:
                    rvars[vn('RoSto', best, s)] = 1
                    rvars[vn('RoA', best)] = 1
                    # Agrego la parada a la ruta, todavía no sabemos como se
                    # conectan
                    routes[best][s] = None
            # pprint(stop_route_choice)
            # pprint(rvars)
            # pprint(routes)

            # De cada estudiante, nos fijamos que combinación de parada y ruta tiene
            # mayor valor, y la asignamos ahí
            load = defaultdict(lambda: 0)
            student_stop_route_choice = {}
            for st in student_stop_route:
                # print(st, student_stop_route[st])
                highest = -0.1
                for val, v0, s in student_stop_route[st]:
                    # print(val, v0, s)
                    if val > highest and stop_route_choice[s] == v0:
                        highest = val
                        best = (v0, s)
                # print(best)
                student_stop_route_choice[st] = best
                # print(student_stop_route_choice)
                rvars[vn('RoStoStu', best[0], best[1], st)] = 1
                load[best[0]] += 1
                if load[best[0]] > data.capacity:
                    return
            # pprint(student_stop_route_choice)
            # pprint(onvars)

            # pprint(route_edges)
            school = data.v_index(data.school)
            total_cost = 0
            rank = defaultdict(lambda: 0)
            for v0 in edges_cost:
                routes[v0][v0] = school
                # print(routes[v0])
                out_of_tour = set(routes[v0].keys())
                out_of_tour.difference_update([v0])
                # print(out_of_tour)

                while len(out_of_tour) > 0:
                    best = (float('+inf'), 0, 0)
                    for v in out_of_tour:
                        vi = v0
                        while vi != school:
                            vnext = routes[v0][vi]
                            new_cost = (
                                edges_cost[v0][vi][v] + edges_cost[v0][v][vnext] -
                                edges_cost[v0][v][vnext],
                                vi, v)
                            # print(new_cost)
                            best = min(best, new_cost)
                            vi = routes[v0][vi]
                    # print(best)
                    _, vi, v = best
                    vnext = routes[v0][vi]
                    # print("AGREGO", v, "DESPUES DE", vi, "ANTES DE", vnext)
                    routes[v0][v] = vnext
                    routes[v0][vi] = v
                    out_of_tour.remove(v)

                rvars[vn('Rank', v0, v0)] = 1
                v = v0
                while v != data.v_index(data.school):
                    rvars[vn("RoEd", v0, v, routes[v0][v])] = 1
                    rvars[vn('Rank', v0, routes[v0][v])
                          ] = rvars[vn('Rank', v0, v)] + 1
                    total_cost += data.dist[data.vdictinv[v]
                                            ][data.vdictinv[routes[v0][v]]]
                    if total_cost >= self.get_incumbent_objective_value()-.01:
                        return
                    v = routes[v0][v]
                # print(v0, routes[v0])

            # pprint(rvars)
            res = [[v[0] for v in variables], [
                rvars[v[0]] for v in variables]]
            print(total_cost, self.get_incumbent_objective_value())
            self.set_solution(res, objective_value=total_cost)
    problem.register_callback(NodeHeuristicCallback)


if options.heur:
    heur = CoolHeuristic(data)
    sol = heur.precalc_varset([v[0] for v in variables], True)
    problem.MIP_starts.add(sol, problem.MIP_starts.effort_level.auto, "cool")

problem.solve()
print("BEST OBJ: ", problem.solution.get_objective_value())
sol = problem.solution.get_values()
dsol = {variables[i][0]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}


gs = {v0: defaultdict(lambda: {}) for v0 in data.depots}
assignment = {}
for vname in dsol:
    sp = vname.split("_")
    if sp[0] == 'RoEd':
        v0, i, j = map(int, sp[1:])
        gs[data.vdictinv[v0]][data.vdictinv[i]][data.vdictinv[j]
                                                ] = data.path[data.vdictinv[i]][data.vdictinv[j]]
    elif sp[0] == 'RoStoStu':
        v0, s, st = map(int, sp[1:])
        assignment[data.students[st]] = data.vdictinv[s]

if True:
    assignment = assign_students_mip(data, gs)

data.add_solution(assignment, gs)
data.write_solution(options.out_file)
