
import cplex
from collections import defaultdict, deque, Counter
from sys import argv
from utils import dist, old_product_constraints
from heuristics import alternative_graphs, heuristic_sbrp, heuristic_alternative_2
from pprint import pprint

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
    clusters = Counter([tuple(v) for k, v in std_stp.items()])
    # pprint(clusters)
    stop_to_stop_cluster = {
        s: [c for c in clusters if s in c] for s in range(len(stops))}
    # print(stop_to_stop_cluster)
    depots = eval(ls[3])
    capacity = eval(ls[4])
    g = eval(ls[5])
    # print(g)


problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)

EXTRA_BUS_COST = 0

vnames = ['students_stop_cluster_' + str(v) + '_' + str(c)
          for v in range(len(stops)) for c in stop_to_stop_cluster[v]] + \
    ["edge_" + str(v1) + "_" + str(v2)
     for v1 in g for v2 in g] + \
    ["edgeload_" + str(v1) + "_" + str(v2)
     for v1 in g for v2 in g] + \
    ["stop_" + str(v) for v in g] + \
    ["stopload_" + str(v) for v in g] + \
    ["buses"]

vtypes = [problem.variables.type.integer
          for v in range(len(stops)) for c in stop_to_stop_cluster[v]] + \
    [problem.variables.type.binary for v1 in g for v2 in g] + \
    [problem.variables.type.integer for v1 in g for v2 in g] + \
    [problem.variables.type.binary for v in g] + \
    [problem.variables.type.integer for v in g] + \
    [problem.variables.type.integer]

vub = [clusters[c] for v in range(len(stops)) for c in stop_to_stop_cluster[v]] + \
    [1 for v1 in g for v2 in g] + \
    [capacity for v1 in g for v2 in g] + \
    [1 for v in g] + \
    [capacity for v in g] + \
    [len(stops)]

vobj = [0 for v in range(len(stops)) for c in stop_to_stop_cluster[v]] + \
    [g[v1][v2][0] for v1 in g for v2 in g] + \
    [0 for v1 in g for v2 in g] + \
    [0 for v in g] + [0 for v in g] + \
    [EXTRA_BUS_COST]

# print(vtypes, vnames, vobj)

problem.variables.add(obj=vobj,
                      lb=None,
                      ub=vub,
                      types=vtypes,
                      names=vnames)

print("VARIABLES")

rhs = [0]
sense = ['E']
constraint = [[
    ["edge_" + str(d) + "_" + str(v2) for d in depots for v2 in g if v2 not in depots] +
    ["edge_" + str(v2) + "_" + str(d) for d in depots for v2 in g if v2 not in depots] +
    ["buses"],
    [1 for d in depots for v2 in g if v2 not in depots] +
    [-1 for d in depots for v2 in g if v2 not in depots] +
    [-1]
]]
problem.linear_constraints.add(lin_expr=constraint,
                               senses=sense,
                               rhs=rhs)

# All degrees but school are <= 1
rhs = [1, 1] * (len(stops) - 1)
sense = ['L', 'L'] * (len(stops) - 1)
constraints = [
    [["edge_" + str(v) + "_" + str(v2) for v2 in g],
     [1 for v2 in g]]
    for v in g if v != 0]

constraints += [
    [["edge_" + str(v2) + "_" + str(v) for v2 in g],
     [1 for v2 in g]]
    for v in g if v != 0]

problem.linear_constraints.add(lin_expr=constraints,
                               senses=sense,
                               rhs=rhs)

# out degree of depots >= in degree
rhs = [0] * len(depots)
sense = ['G'] * len(depots)
constraints = [[
    ["edge_" + str(v) + "_" + str(v2) for v2 in g if v != v2] +
    ["edge_" + str(v2) + "_" + str(v) for v2 in g if v != v2],
    [1 for v2 in g if v != v2] + [-1 for v2 in g if v != v2]
] for v in depots]

problem.linear_constraints.add(lin_expr=constraints,
                               senses=sense,
                               rhs=rhs)

# degree of common stops
rhs = [0] * (len(stops) - len(depots) - 1)
sense = ['E'] * (len(stops) - len(depots) - 1)
constraints = [[
    ["edge_" + str(v) + "_" + str(v2) for v2 in g if v != v2] +
    ["edge_" + str(v2) + "_" + str(v) for v2 in g if v != v2],
    [1 for v2 in g if v != v2] + [-1 for v2 in g if v != v2]
] for v in g if v not in depots + [0]]

problem.linear_constraints.add(lin_expr=constraints,
                               senses=sense,
                               rhs=rhs)

# Degree of school
rhs = [0, len(depots)]
sense = ['E', 'L']
constraints = [
    [["edge_" + str(0) + "_" + str(v2) for v2 in g], [1 for v2 in g]],
    [["edge_" + str(v2) + "_" + str(0) for v2 in g], [1 for v2 in g]]
]
problem.linear_constraints.add(lin_expr=constraints,
                               senses=sense,
                               rhs=rhs)
# print("DEGREES")

# # If students > 0 go to stop, bus must stop there
rhs = [0 for v in g for c in stop_to_stop_cluster[v]]
sense = ['G' for v in g for c in stop_to_stop_cluster[v]]
constraint = [[
    ["edge_" + str(v) + "_" + str(v2) for v2 in g] +
    ["students_stop_cluster_" + str(v) + '_' + str(c)],
    [len(students) for v2 in g] + [-1]
] for v in g for c in stop_to_stop_cluster[v]]

problem.linear_constraints.add(lin_expr=constraint,
                               senses=sense,
                               rhs=rhs)
print("STOP STUDENT BINDING")

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
print("1-LOOPS")

# # All clusters add up
rhs = [clusters[c] for c in clusters]
sense = ['E'] * len(clusters)
constraint = [[
    ["students_stop_cluster_" + str(v) + '_' + str(c) for v in c],
    [1 for v in c]
] for c in clusters]

problem.linear_constraints.add(lin_expr=constraint,
                               senses=sense,
                               rhs=rhs)
print("CLUSTERS")

# # Bus stops
rhs = [0] * len(stops)
sense = ['E'] * len(stops)
constraint = [[
    ["edge_" + str(sp_i) + "_" + str(v) for v in range(len(stops))] +
    ['stop_' + str(sp_i)],
    [1 for v in range(len(stops))] + [-1]
] for sp_i in g]
problem.linear_constraints.add(lin_expr=constraint,
                               senses=sense,
                               rhs=rhs)
print("STOP EDGE BINDING")

# Edge loads
rhss = []
senses = []
constraints = []
for v1 in g:
    for v2 in g:
        rhs, sense, constraint = old_product_constraints(
            'edgeload_' + str(v1) + '_' + str(v2),
            'edge_' + str(v1) + '_' + str(v2),
            'stopload_' + str(v1),
            len(students)
        )
        rhss += rhs
        senses += sense
        constraints += constraint

problem.linear_constraints.add(lin_expr=constraints,
                               senses=senses,
                               rhs=rhss)

# # Stoploads non-depots
k = len(stops) - 1
rhs = [0] * k
sense = ['E'] * k
constraint = [[
    ['students_stop_cluster_' + str(v) + '_' + str(c) for c in stop_to_stop_cluster[v]] +
    ['edgeload_' + str(v2) + '_' + str(v) for v2 in g] +
    ['stopload_' + str(v)],
    [1 for c in stop_to_stop_cluster[v]] + [1 for v2 in g] + [-1]
] for v in g if v != 0]
problem.linear_constraints.add(lin_expr=constraint,
                               senses=sense,
                               rhs=rhs)

print("LOADS")

# class CutCallback(cplex.callbacks.CutCallback):
#     def __call__(self):


# heur = heuristic_alternative_2(stops, students, max_walk_dist, std_stp, stp_std,
#                                clusters, stop_to_stop_cluster, depots, capacity, g)
# problem.MIP_starts.add(heur,
#                        problem.MIP_starts.effort_level.repair, "heur")
problem.solve()
# problem.conflict.refine_MIP_start(0, problem.conflict.all_constraints())
# problem.conflict.write('conflicto')

print("BEST OBJ: ", problem.solution.get_objective_value())
sol = problem.solution.get_values()
# print(sol)
dsol = {vnames[i]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}
pprint(dsol)
gs = alternative_graphs(vnames, sol, depots, g)

with open(argv[2], 'w') as f:
    f.write(str(dict(gs)) + '\n')
# sdict = {}
# for i in range(len(students)):
#     key = [k for k in dsol if k.startswith('student_stop_' + str(i))][0]
#     stop = int(key.split('_')[3])
#     sdict[i] = stop
# f.write(str(sdict) + '\n')
