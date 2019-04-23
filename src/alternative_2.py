
import cplex
from collections import defaultdict, deque, Counter
from heapq import *
from sys import argv
from utils import dist, alternative_graphs, heuristic_sbrp, product_constraints, heuristic_alternative

# INPUT
with open(argv[1], 'r') as f:
    ls = f.readlines()
    stops = eval(ls[0])
    students = eval(ls[1])
    max_walk_dist = eval(ls[2])
    std_stp = {k: [v for v in range(1, len(stops)) if dist(
        stops[v], students[k]) <= max_walk_dist] for k in range(len(students))}
    stp_std = {k: [v for v in range(len(students)) if k in std_stp[v]]
               for k in range(1, len(stops))}
    clusters = set([tuple(v) for k, v in std_stp.items()])
    stop_to_stop_cluster = {
        s: [c for c in clusters if s in c] for s in range(len(stops))}
    # print(stop_to_stop_cluster)
    depots = eval(ls[3])
    capacity = eval(ls[4])
    g = eval(ls[5])
    # print(g)


problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)

vnames = ['students_stop_cluster_' + str(v) + '_' + str(c)
          for v in range(len(stops)) for c in stop_to_stop_cluster[v]] + \
    ["edge_" + str(v1) + "_" + str(v2)
     for v1 in g for v2 in g] + \
    ["edgeload_" + str(v1) + "_" + str(v2)
     for v1 in g for v2 in g] + \
    ["stop_" + str(v) for v in g] + \
    ["stopload_" + str(v) for v in g]


# heur = heuristic_alternative(stops, students, max_walk_dist, std_stp,
#                              stp_std, depots, capacity, g)

vtypes = [problem.variables.type.integer
          for v in range(len(stops)) for c in stop_to_stop_cluster[v]] + \
    [problem.variables.type.binary for v1 in g for v2 in g] + \
    [problem.variables.type.integer for v1 in g for v2 in g] + \
    [problem.variables.type.binary for v in g] + \
    [problem.variables.type.integer for v in g]

vobj = [0 for v in range(len(stops)) for c in stop_to_stop_cluster[v]] + \
    [g[v1][v2] for v1 in g for v2 in g] + \
    [0 for v1 in g for v2 in g] + \
    [0 for v in g] + [0 for v in g]

# print(vtypes, vnames, vobj)

problem.variables.add(obj=vobj,
                      lb=None,
                      ub=None,
                      types=vtypes,
                      names=vnames)


# Degree of depots
for v in depots:
    rhs = [1, 0]
    sense = ['E', 'E']
    constraints = [
        [["edge_" + str(v) + "_" + str(v2) for v2 in g], [1 for v2 in g]],
        [["edge_" + str(v2) + "_" + str(v) for v2 in g], [1 for v2 in g]]
    ]
    # print(constraints)
    problem.linear_constraints.add(lin_expr=constraints,
                                   senses=sense,
                                   rhs=rhs,
                                   names=['depot_dout_' + str(v),
                                          'depot_din_' + str(v)])


# Degree of school
rhs = [0, len(depots)]
sense = ['E', 'E']
constraints = [
    [["edge_" + str(0) + "_" + str(v2) for v2 in g], [1 for v2 in g]],
    [["edge_" + str(v2) + "_" + str(0) for v2 in g], [1 for v2 in g]]
]
problem.linear_constraints.add(lin_expr=constraints,
                               senses=sense,
                               rhs=rhs)

# Other degrees
for v in g:
    if v in depots + [0]:
        continue

    rhs = [0]
    sense = ['E']
    constraints = [
        [["edge_" + str(v) + "_" + str(v2) for v2 in g if v != v2] +
         ["edge_" + str(v2) + "_" + str(v) for v2 in g if v != v2],
         [1 for v2 in g if v != v2] + [-1 for v2 in g if v != v2]]
    ]
    problem.linear_constraints.add(lin_expr=constraints,
                                   senses=sense,
                                   rhs=rhs)

# If students > 0 go to stop, bus must stop there
for v in g:
    for c in stop_to_stop_cluster[v]:
        rhs = [0]
        sense = ['G']
        constraint = [
            ["edge_" + str(v) + "_" + str(v2) for v2 in g] +
            ["students_stop_cluster_" + str(v) + '_' + str(c)],
            [len(students) for v2 in g] + [-1]
        ]
        problem.linear_constraints.add(lin_expr=[constraint],
                                       senses=sense,
                                       rhs=rhs)

# 1-loops
rhs = [0]
sense = ['E']
constraint = [
    ["edge_" + str(v) + "_" + str(v) for v in g],
    [1 for v in g]
]
problem.linear_constraints.add(lin_expr=[constraint],
                               senses=sense,
                               rhs=rhs)

# All clusters add up
for c in clusters:
    rhs = [len(c)]
    sense = ['E']
    constraint = [
        ["students_stop_cluster_" + str(v) + '_' + str(c) for v in c],
        [1 for v in c]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

# Bus stops
for sp_i in range(len(stops)):
    rhs = [0]
    sense = 'E'
    constraint = [
        ["edge_" + str(sp_i) + "_" + str(v) for v in range(len(stops))] +
        ['stop_' + str(sp_i)],
        [1 for v in range(len(stops))] + [-1]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

# Stopload depots
for b in depots:
    rhs = [0]
    sense = ['E']
    constraint = [
        ['students_stop_cluster_' + str(b) + '_' + str(c) for c in stop_to_stop_cluster[b]] +
        ['stopload_' + str(b)],
        [1 for c in stop_to_stop_cluster[b]] + [-1]
    ]
    # print(constraint)
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

# Edge loads
for v1 in g:
    for v2 in g:
        rhs, sense, constraint = product_constraints(
            'edgeload_' + str(v1) + '_' + str(v2),
            'edge_' + str(v1) + '_' + str(v2),
            'stopload_' + str(v1),
            len(students)
        )
        problem.linear_constraints.add(lin_expr=constraint,
                                       senses=sense,
                                       rhs=rhs)

# Stoploads non-depots
for v in g:
    if v in depots + [0]:
        continue
    rhs = [0]
    sense = ['E']
    constraint = [
        ['students_stop_cluster_' + str(v) + '_' + str(c) for c in stop_to_stop_cluster[v]] +
        ['edgeload_' + str(v2) + '_' + str(v) for v2 in g] +
        ['stopload_' + str(v)],
        [1 for c in stop_to_stop_cluster[v]] + [1 for v2 in g] + [-1]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

# Capacity
for v in g:
    for v2 in g:
        rhs = [capacity]
        sense = ['L']
        constraint = [['edgeload_' + str(v) + '_' + str(v2)], [1]]
        problem.linear_constraints.add(lin_expr=[constraint],
                                       senses=sense,
                                       rhs=rhs)


problem.write('example.lp')
print('WRITTEN')
# problem.MIP_starts.add(heur,
#                        problem.MIP_starts.effort_level.auto, "heur")
problem.solve()
print("BEST OBJ: ", problem.solution.get_objective_value())
sol = problem.solution.get_values()
# print(sol)
dsol = {vnames[i]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}
for k, v in dsol.items():
    print(k, v)
gs = alternative_graphs(vnames, sol, depots, g)

with open(argv[2], 'w') as f:
    f.write(str(dict(gs)) + '\n')
    sdict = {}
    # for i in range(len(students)):
    #     key = [k for k in dsol if k.startswith('student_stop_' + str(i))][0]
    #     stop = int(key.split('_')[3])
    #     sdict[i] = stop
    # f.write(str(sdict) + '\n')
