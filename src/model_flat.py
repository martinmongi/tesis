import re
from collections import Counter, defaultdict, deque
from pprint import pprint
from sys import argv
from optparse import OptionParser
from heuristics import insertion_flat_wrapper
from student_assignment import assign_students_mip

import cplex

from utils import (ProblemData, bfs, dist, old_product_constraints, transpose,
                   vn)

parser = OptionParser()
parser.add_option("--if", dest="in_file")
parser.add_option("--of", dest="out_file")
parser.add_option("--grouped", dest="grouped", action="store_true")
(options, args) = parser.parse_args()

# INPUT
data = ProblemData(options.in_file)

problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)
problem.parameters.dettimelimit.set(1000000)
problem.parameters.timelimit.set(600)

variables = [(vn('Edge', data.v_index(v1), data.v_index(v2)), 'B', data.dist[v1][v2])
             for v1 in data.stops for v2 in data.stops if v1 != v2] + \
    [(vn('EdgeLoad', data.v_index(v1), data.v_index(v2)), 'C', 0)
     for v1 in data.stops
     for v2 in data.stops if v1 != v2] + \
    [(vn('Stop', data.v_index(v1)), 'B', 0)
     for v1 in data.stops[1:]] + \
    [(vn('StopLoad', data.v_index(v1)), 'C', 0)
     for v1 in data.stops] + \
    [(vn('RouteActive', data.v_index(v0)), 'B', 0)
     for v0 in data.depots]

if options.grouped:
    variables += [(vn('StopCluster', data.v_index(v1), list(map(data.v_index, c))), 'I', 0)
                  for v1 in data.stops for c in data.stop_to_clusters[v1]]

else:
    variables += [(vn('StopStudent', data.v_index(v1), data.s_index(s)), 'B', 0)
                  for s in data.students for v1 in data.student_to_stop[s]]

problem.variables.add(obj=[v[2] for v in variables],
                      types=[v[1] for v in variables],
                      names=[v[0] for v in variables])

# All vertices have equal in and out degree, other than depots on their own tour
# or school in all depots
rhs = [0 for v in data.stops if v not in [data.school] + data.depots]
sense = ['E' for v in data.stops if v not in [data.school] + data.depots]
constraint = [[
    [vn('Edge', data.v_index(v), data.v_index(v2))
     for v2 in data.stops if v != v2] +
    [vn('Edge', data.v_index(v2), data.v_index(v))
     for v2 in data.stops if v != v2],
    [1 for v2 in data.stops if v != v2] +
    [-1 for v2 in data.stops if v != v2]
] for v in data.stops if v not in [data.school] + data.depots]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# outdeg - indeg = routeactive
# All depots have 0 <= outdeg - indeg <= 1 in their own tours (constrainted by binarity of routeactive)
rhs = [0] * len(data.depots)
sense = ['E'] * len(data.depots)
constraint = [[
    [vn('Edge', data.v_index(v0), data.v_index(v2))
     for v2 in data.stops if v2 != v0] +
    [vn('Edge', data.v_index(v2), data.v_index(v0))
     for v2 in data.stops if v2 != v0] +
    [vn('RouteActive', data.v_index(v0))],
    [1 for v2 in data.stops if v2 != v0] +
    [-1 for v2 in data.stops if v2 != v0] +
    [-1]
] for v0 in data.depots]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# outdeg - indeg = - routeactive
# School has -1 <= outdeg - indeg <= 0 for all tours (constrained by binarity of routeactive)
rhs = [0]
sense = ['E']
constraint = [[
    [vn('Edge', data.v_index(data.school), data.v_index(v2))
     for v2 in data.stops if v2 != data.school] +
    [vn('Edge', data.v_index(v2), data.v_index(data.school))
     for v2 in data.stops if v2 != data.school] +
    [vn('RouteActive', data.v_index(v0)) for v0 in data.depots],
    [1 for v2 in data.stops if v2 != data.school] +
    [-1 for v2 in data.stops if v2 != data.school] +
    [1 for v0 in data.depots]
]]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# Having out degree means vertex in stops can have stop
rhs = [0 for v in data.stops[1:]]
sense = ['E' for v in data.stops[1:]]
constraint = [[
    [vn('Edge', data.v_index(v), data.v_index(v2))
     for v2 in data.stops if v2 != v] +
    [vn('Stop', data.v_index(v))],
    [1 for v2 in data.stops if v2 != v] + [-1]
] for v in data.stops[1:]]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

if options.grouped:
    # Cluster choices add to cluster size
    rhs = [data.clusters[c] for c in data.clusters]
    sense = ['E' for c in data.clusters]
    constraint = [[
        [vn('StopCluster', data.v_index(
            v1), list(map(data.v_index, c))) for v1 in c],
        [1 for v1 in c]
    ] for c in data.clusters]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # If cluster to stop, route is larger than 1, stop,route must be active
    rhs = [0 for v1 in data.stops for c in data.stop_to_clusters[v1]]
    sense = [
        'L' for v1 in data.stops for c in data.stop_to_clusters[v1]]
    constraint = [[
        [vn('StopCluster', data.v_index(v1), list(map(data.v_index, c))),
         vn('Stop', data.v_index(v1))],
        [1, - data.clusters[c]]
    ] for v1 in data.stops for c in data.stop_to_clusters[v1]]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # Load variables
    rhs = [0 for v in data.stops]
    sense = ['E' for v in data.stops]
    constraint = [[
        [vn('StopCluster', data.v_index(v), list(map(data.v_index, c)))
         for c in data.stop_to_clusters[v]] +
        [vn('EdgeLoad', data.v_index(v2), data.v_index(v))
         for v2 in data.stops if v2 != v] +
        [vn('StopLoad', data.v_index(v))],
        [1 for c in data.stop_to_clusters[v]] +
        [1 for v2 in data.stops if v2 != v] + [-1]
    ] for v in data.stops]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                                   names=[vn('StopLoad', data.v_index(v)) for v in data.stops])

else:
    # Stop choices for each student add to 1
    rhs = [1 for s in data.students]
    sense = ['E' for s in data.students]
    constraint = [[
        [vn('StopStudent', data.v_index(v1), data.s_index(s))
        for v1 in data.student_to_stop[s]],
        [1 for v1 in data.student_to_stop[s]],
    ] for s in data.students]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # If student chooses stop, it must be in a tour
    rhs = [0 for s in data.students for v in data.student_to_stop[s]]
    sense = ['L' for s in data.students for v in data.student_to_stop[s]]
    constraint = [[
        [vn('StopStudent', data.v_index(v), data.s_index(s)),
        vn('Stop', data.v_index(v))],
        [1, -1]
    ] for s in data.students for v in data.student_to_stop[s]]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    # Load variables
    rhs = [0 for v in data.stops]
    sense = ['E' for v in data.stops]
    constraint = [[
        [vn('StopStudent', data.v_index(v), data.s_index(s))
        for s in data.stop_to_students[v]] +
        [vn('EdgeLoad', data.v_index(v2), data.v_index(v))
        for v2 in data.stops if v2 != v] +
        [vn('StopLoad', data.v_index(v))],
        [1 for s in data.stop_to_students[v]] +
        [1 for v2 in data.stops if v2 != v] + [-1]
    ] for v in data.stops]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs,
                                names=[vn('StopLoad', data.v_index(v)) for v in data.stops])

rhss = []
senses = []
constraints = []

for v1 in data.stops:
    for v2 in data.stops:
        if v1 == v2:
            continue
        rhs, sense, constraint = old_product_constraints(
            vn('EdgeLoad', data.v_index(v1), data.v_index(v2)),
            vn('Edge', data.v_index(v1), data.v_index(v2)),
            vn('StopLoad', data.v_index(v1)),
            len(data.students)
        )
        rhss += rhs
        senses += sense
        constraints += constraint
problem.linear_constraints.add(lin_expr=constraints, senses=senses, rhs=rhss)

rhs = [data.capacity for v1 in data.stops for v2 in data.stops if v1 != v2]
sense = ['L' for v1 in data.stops for v2 in data.stops if v1 != v2]
constraint = [[
    [vn('EdgeLoad', data.v_index(v1), data.v_index(v2))],
    [1]
] for v1 in data.stops for v2 in data.stops if v1 != v2]
problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

# ins_heur = insertion_flat_wrapper(data, [v[0] for v in variables])
# if ins_heur:
#     problem.MIP_starts.add(ins_heur,
#                            problem.MIP_starts.effort_level.auto, "insertion")

problem.solve()
print("BEST OBJ: ", problem.solution.get_objective_value())
sol = problem.solution.get_values()
dsol = {variables[i][0]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}
# pprint(dsol)

gs = {data.school: defaultdict(lambda: {})}
assignment = {}
for vname in dsol:
    sp = vname.split("_")
    if sp[0] == 'RouteActive':
        gs[data.vdictinv[int(sp[1])]] = defaultdict(lambda: {})
    if sp[0] == 'Edge':
        i, j = map(int, sp[1:])
        gs[data.school][data.vdictinv[i]][data.vdictinv[j]
                                          ] = data.path[data.vdictinv[i]][data.vdictinv[j]]
    elif sp[0] == 'StopStudent':
        s, st = map(int, sp[1:])
        assignment[data.students[st]] = data.vdictinv[s]

for r in gs:
    v = r
    while v != data.school:
        nxt,val = gs[data.school][v].popitem()
        gs[r][v][nxt] = val
        v = nxt
del gs[data.school]

# if options.grouped:
#     assignment = assign_students_mip(data, gs)

data.add_solution(assignment, gs)
data.write_solution(options.out_file)
