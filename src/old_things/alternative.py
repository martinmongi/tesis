
import cplex
from collections import defaultdict, deque, Counter
from heapq import *
from sys import argv
from utils import dist, old_product_constraints
from heuristics import alternative_graphs, heuristic_sbrp, heuristic_alternative
# INPUT
with open(argv[1], 'r') as f:
    ls = f.readlines()
    stops = eval(ls[0])
    students = eval(ls[1])
    max_walk_dist = eval(ls[2])
    std_stp = {k: [v for v in range(1,len(stops)) if dist(
        stops[v], students[k]) <= max_walk_dist] for k in range(len(students))}
    stp_std = {k: [v for v in range(len(students)) if k in std_stp[v]]
               for k in range(1,len(stops))}
    # print(std_stp)
    # print(stp_std)
    depots = eval(ls[3])
    capacity = eval(ls[4])
    g = eval(ls[5])


problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)

vnames = ['student_stop_' + str(std_i) + '_' + str(stp_i)
          for std_i in std_stp for stp_i in std_stp[std_i]] + \
    ["edge_" + str(v1) + "_" + str(v2)
     for v1 in g for v2 in g] + \
    ["edgeload_" + str(v1) + "_" + str(v2)
     for v1 in g for v2 in g] + \
    ["stop_" + str(v) for v in g] + \
    ["stopload_" + str(v) for v in g]
# print(vnames)

heur = heuristic_alternative(stops, students, max_walk_dist, std_stp,
                             stp_std, depots, capacity, g)

vtypes = [problem.variables.type.binary
          for std_i in std_stp for stp_i in std_stp[std_i]] + \
    [problem.variables.type.binary for v1 in g for v2 in g] + \
    [problem.variables.type.integer for v1 in g for v2 in g] + \
    [problem.variables.type.binary for v in g] + \
    [problem.variables.type.integer for v in g]

vobj = [0 for std_i in std_stp for stp_i in std_stp[std_i]] + \
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

# If student goes to stop, bus must stop there
for s in range(len(students)):
    for v in std_stp[s]:
        rhs = [0]
        sense = ['G']
        constraint = [
            ["edge_" + str(v) + "_" + str(v2) for v2 in g] +
            ["student_stop_" + str(s) + "_" + str(v)],
            [1 for v2 in g] + [-1]
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

# All students go to a stop
for s in range(len(students)):
    rhs = [1]
    sense = ['E']
    constraint = [
        ['student_stop_' + str(s) + '_' + str(stop)
         for stop in std_stp[s]],
        [1 for stop in std_stp[s]]
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
        ['student_stop_' + str(s) + '_' + str(b) for s in stp_std[b]] +
        ['stopload_' + str(b)],
        [1 for s in stp_std[b]] + [-1]
    ]
    # print(constraint)
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

# Edge loads
for v1 in g:
    for v2 in g:
        rhs, sense, constraint = old_product_constraints(
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
        ['student_stop_' + str(s) + '_' + str(v) for s in stp_std[v]] +
        ['edgeload_' + str(v2) + '_' + str(v) for v2 in g] +
        ['stopload_' + str(v)],
        [1 for s in stp_std[v]] + [1 for v2 in g] + [-1]
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
problem.MIP_starts.add(heur,
                       problem.MIP_starts.effort_level.auto, "heur")
problem.solve()
print("BEST OBJ: ", problem.solution.get_objective_value())
exit()
sol = problem.solution.get_values()
# print(sol)
dsol = {vnames[i]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}
for k, v in dsol.items():
    print(k, v)
gs = alternative_graphs(vnames, sol, depots, g)

with open(argv[2], 'w') as f:
    f.write(str(dict(gs)) + '\n')
    sdict = {}
    for i in range(len(students)):
        key = [k for k in dsol if k.startswith('student_stop_' + str(i))][0]
        stop = int(key.split('_')[3])
        sdict[i] = stop
    f.write(str(sdict) + '\n')
