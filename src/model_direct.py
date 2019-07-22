import re
from collections import Counter, defaultdict, deque
from pprint import pprint
from sys import argv
from optparse import OptionParser
from heuristics import insertion_direct_wrapper
from student_assignment import assign_students_mip
from utils import avg_point, haversine_dist

import cplex

from utils import (ProblemData, bfs, dist, old_product_constraints, transpose,
                   vn, haversine_dist)

parser = OptionParser()
parser.add_option("--if", dest="in_file")
parser.add_option("--of", dest="out_file")
parser.add_option("--grouped", dest="grouped", action="store_true")
(options, args) = parser.parse_args()

# INPUT
data = ProblemData(options.in_file)
problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)

variables = [(vn('RouteEdge', data.v_index(v0), data.v_index(v1), data.v_index(v2)), 'I', data.original_graph[v1][v2][0])
             for v0 in data.depots for v1 in data.original_graph for v2 in data.original_graph[v1]] + \
    [(vn('RouteStop', data.v_index(v0), data.v_index(v1)), 'B', 0)
     for v0 in data.depots for v1 in data.stops[1:]] + \
    [(vn('RouteActive', data.v_index(v0)), 'B', 0) for v0 in data.depots]

if options.grouped:
    variables += [(vn('RouteStopCluster', data.v_index(v0), data.v_index(v1), list(map(data.v_index, c))), 'I', .00 * haversine_dist(v1,avg_point(data.cluster_to_students[c])))
                  for v0 in data.depots for v1 in data.stops for c in data.stop_to_clusters[v1]]
else:
    variables += [(vn('RouteStopStudent', data.v_index(v0), data.v_index(v1), data.s_index(s)), 'B', 0)
                  for s in data.students for v0 in data.depots for v1 in data.student_to_stop[s]]

problem.variables.add(obj=[v[2] for v in variables],
                      types=[v[1] for v in variables],
                      names=[v[0] for v in variables])

# Upper bound on edges
rhs = [data.edge_max_flow[v1, v2]
       for v1 in data.original_graph
       for v2 in data.original_graph[v1]]
sense = ['L' for v1 in data.original_graph for v2 in data.original_graph[v1]]
constraint = [[
    [vn('RouteEdge', data.v_index(v0), data.v_index(v1), data.v_index(v2))
     for v0 in data.depots],
    [1 for v0 in data.depots]
] for v1 in data.original_graph for v2 in data.original_graph[v1]]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                               names=[vn('BoundOnEdge', data.v_index(v1),
                                         data.v_index(v2))
                                      for v1 in data.original_graph
                                      for v2 in data.original_graph[v1]])

# All vertices have equal in and out degree, other than depots on their own tour
# or school in all depots
rhs = [0 for v0 in data.depots for v in data.original_graph
       if v not in [data.school, v0]]
sense = ['E' for v0 in data.depots for v in data.original_graph
         if v not in [data.school, v0]]
constraint = [[
    [vn('RouteEdge', data.v_index(v0), data.v_index(v), data.v_index(v2))
     for v2 in data.original_graph[v]] +
    [vn('RouteEdge', data.v_index(v0), data.v_index(v2), data.v_index(v))
     for v2 in data.reverse_original_graph[v]],
    [1 for v2 in data.original_graph[v]] +
    [-1 for v2 in data.reverse_original_graph[v]]
] for v0 in data.depots for v in data.original_graph if v not in [data.school, v0]]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                               names=[vn('RouteInOutBalance', data.v_index(v0),
                                         data.v_index(v)) for v0 in data.depots
                                      for v in data.original_graph
                                      if v not in [data.school, v0]])

# outdeg - indeg = routeactive
# All depots have 0 <= outdeg - indeg <= 1 in their own tours (constrainted by binarity of routeactive)
rhs = [0] * len(data.depots)
sense = ['E'] * len(data.depots)
constraint = [[
    [vn('RouteEdge', data.v_index(v0), data.v_index(v0), data.v_index(v2))
     for v2 in data.original_graph[v0]] +
    [vn('RouteEdge', data.v_index(v0), data.v_index(v2), data.v_index(v0))
     for v2 in data.reverse_original_graph[v0]] +
    [vn('RouteActive', data.v_index(v0))],
    [1 for v2 in data.original_graph[v0]] +
    [-1 for v2 in data.reverse_original_graph[v0]] +
    [-1]
] for v0 in data.depots]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                               names=[vn('RouteActiveDepots', data.v_index(v0))
                                      for v0 in data.depots])

# outdeg - indeg = - routeactive
# School has -1 <= outdeg - indeg <= 0 for all tours (constrained by binarity of routeactive)
rhs = [0] * len(data.depots)
sense = ['E'] * len(data.depots)
constraint = [[
    [vn('RouteEdge', data.v_index(v0), data.v_index(data.school), data.v_index(v2))
     for v2 in data.original_graph[data.school]] +
    [vn('RouteEdge', data.v_index(v0), data.v_index(v2), data.v_index(data.school))
     for v2 in data.reverse_original_graph[data.school]] +
    [vn('RouteActive', data.v_index(v0))],
    [1 for v2 in data.original_graph[data.school]] +
    [-1 for v2 in data.reverse_original_graph[data.school]] +
    [1]
] for v0 in data.depots]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                               names=[vn('RouteActiveSchool', data.v_index(v0))
                                      for v0 in data.depots])


# Having out degree means vertex in stops can have stop
rhs = [0 for v0 in data.depots for v in data.stops[1:]]
sense = ['G' for v0 in data.depots for v in data.stops[1:]]
constraint = [[
    [vn('RouteEdge', data.v_index(v0), data.v_index(v), data.v_index(v2))
     for v2 in data.original_graph[v]] +
    [vn('RouteStop', data.v_index(v0), data.v_index(v))],
    [1 for v2 in data.original_graph[v]] + [-1]
] for v0 in data.depots for v in data.stops[1:]]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                               names=[vn('EdgeStopBinding', data.v_index(v0), data.v_index(v))
                                      for v0 in data.depots for v in data.stops[1:]])

# All stops can be visited at most one time
rhs = [1 for v in data.stops[1:]]
sense = ['L' for v in data.stops[1:]]
constraint = [[
    [vn('RouteStop', data.v_index(v0), data.v_index(v)) for v0 in data.depots],
    [1 for v0 in data.depots]
] for v in data.stops[1:]]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                               names=[vn('RouteStopSum', data.v_index(v))
                                      for v in data.stops[1:]])

if options.grouped:
    # Cluster choices add to cluster size
    rhs = [data.clusters[c] for c in data.clusters]
    sense = ['E' for c in data.clusters]
    constraint = [[
        [vn('RouteStopCluster', data.v_index(v0), data.v_index(
            v1), list(map(data.v_index, c))) for v0 in data.depots for v1 in c],
        [1 for v0 in data.depots for v1 in c]
    ] for c in data.clusters]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # If cluster to stop, route is larger than 1, stop,route must be active
    rhs = [0 for v0 in data.depots for v1 in data.stops for c in data.stop_to_clusters[v1]]
    sense = [
        'L' for v0 in data.depots for v1 in data.stops for c in data.stop_to_clusters[v1]]
    constraint = [[
        [vn('RouteStopCluster', data.v_index(v0), data.v_index(v1), list(map(data.v_index, c))),
         vn('RouteStop', data.v_index(v0), data.v_index(v1))],
        [1, - data.clusters[c]]
    ] for v0 in data.depots for v1 in data.stops for c in data.stop_to_clusters[v1]]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # Capacities are kept
    rhs = [data.capacity for v0 in data.depots]
    sense = ['L' for v0 in data.depots]
    constraint = [[
        [vn('RouteStopCluster', data.v_index(v0), data.v_index(v1), list(map(data.v_index, c)))
         for v1 in data.stops for c in data.stop_to_clusters[v1]],
        [1 for v1 in data.stops for c in data.stop_to_clusters[v1]]
    ] for v0 in data.depots]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)
    
else:
    # Stop choices for each student add to 1
    rhs = [1 for s in data.students]
    sense = ['E' for s in data.students]
    constraint = [[
        [vn('RouteStopStudent', data.v_index(v0), data.v_index(v1), data.s_index(s))
        for v0 in data.depots for v1 in data.student_to_stop[s]],
        [1 for v0 in data.depots for v1 in data.student_to_stop[s]],
    ] for s in data.students]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                                names=[vn('StudentStopSum', data.s_index(s))for s in data.students])

    # If student chooses stop, it must be in a tour
    rhs = [0 for s in data.students for v0 in data.depots for v in data.student_to_stop[s]]
    sense = ['L' for s in data.students for v0 in data.depots for v in data.student_to_stop[s]]
    constraint = [[
        [vn('RouteStopStudent', data.v_index(v0), data.v_index(v), data.s_index(s)),
        vn('RouteStop', data.v_index(v0), data.v_index(v))],
        [1, -1]
    ] for s in data.students for v0 in data.depots for v in data.student_to_stop[s]]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # Capacities are kept
    rhs = [data.capacity for v0 in data.depots]
    sense = ['L' for v0 in data.depots]
    constraint = [[
        [vn('RouteStopStudent', data.v_index(v0), data.v_index(v), data.s_index(s))
        for s in data.students for v in data.student_to_stop[s]],
        [1 for s in data.students for v in data.student_to_stop[s]]
    ] for v0 in data.depots]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# If a stop is on, the route should be active
rhs = [0 for v in data.stops[1:] for v0 in data.depots]
sense = ['G' for v in data.stops[1:] for v0 in data.depots]
constraint = [[
    [vn('RouteStop', data.v_index(v0), data.v_index(v)),
     vn('RouteActive', data.v_index(v0))],
    [-1, 1]
] for v in data.stops[1:] for v0 in data.depots]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

class SubToursLazyConstraintCallback(cplex.callbacks.LazyConstraintCallback):

    def __call__(self):
        sols = self.get_values()
        dsol = {variables[i][0]: sols[i] for i in range(len(sols)) if sols[i] > 0.5}
        gs = {data.v_index(v0): defaultdict(lambda: []) for v0 in data.depots}
        for vname in dsol:
            sp = vname.split("_")
            if sp[0] == 'RouteEdge':
                v0, i, j = map(int, sp[1:])
                gs[v0][i].append(j)

        sloops = []
        for v0, g in gs.items():
            main_tour = bfs(g, v0)
            loops = set([v for v in g]).difference(main_tour)
            while len(loops) > 0:
                loop = bfs(g, loops.pop())
                sloops.append(loop)
                loops.difference_update(loop)
        # print(sloops)
        for loop in sloops:
            # if 0 in loop:
            #     continue
            for v in loop:
                if data.vdictinv[v] not in data.stops:
                    continue
                for v0 in data.depots:
                    rhs = 0
                    sense = 'G'
                    constraint = [
                        [vn('RouteEdge', data.v_index(v0), v1, data.v_index(v2))
                         for v1 in loop for v2 in data.original_graph[data.vdictinv[v1]]
                         if data.v_index(v2) not in loop] +
                        [vn('RouteStop', data.v_index(v0), v)],
                        [1 for v1 in loop for v2 in data.original_graph[data.vdictinv[v1]]
                         if data.v_index(v2) not in loop] + [-1]
                    ]
                    # print(constraint)
                    self.add(constraint=constraint,
                             sense=sense,
                             rhs=rhs)


problem.register_callback(SubToursLazyConstraintCallback)

# ins_heur = insertion_direct_wrapper(data, [v[0] for v in variables])
# if ins_heur:
#     problem.MIP_starts.add(ins_heur,
#                            problem.MIP_starts.effort_level.auto, "insertion")

problem.solve()
print("BEST OBJ: ", problem.solution.get_objective_value())
sol = problem.solution.get_values()
dsol = {variables[i][0]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}

# pprint(dsol)
gs = {v0: defaultdict(lambda: {}) for v0 in data.depots}

assignment = {}
for vname in dsol:
    if dsol[vname] < 0.5:
        continue
    sp = vname.split("_")
    if sp[0] == 'RouteEdge':
        v0, i, j = map(int, sp[1:])
        gs[data.vdictinv[v0]][data.vdictinv[i]][data.vdictinv[j]
                                                ] = data.original_graph[data.vdictinv[i]][data.vdictinv[j]][1]
        # print(i, j, dsol[vname], data.edge_max_flow[data.vdictinv[i], data.vdictinv[j]],
        #       dsol[vname] - data.edge_max_flow[data.vdictinv[i], data.vdictinv[j]],
        #       dsol[vname] - data.edge_max_flow[data.vdictinv[i], data.vdictinv[j]] <= 0, sep='\t')
    elif sp[0] == 'RouteStopStudent':
        v0, s, st = map(int, sp[1:])
        assignment[data.students[st]] = data.vdictinv[s]

if options.grouped:
    assignment = assign_students_mip(data, gs)

data.add_solution(assignment, gs)
data.write_solution(options.out_file)
