import cplex
from collections import defaultdict, deque
from heapq import *
from sys import argv
from utils import dist, graphs

# INPUT
with open(argv[1], 'r') as f:
    ls = f.readlines()
    stops = eval(ls[0])
    students = eval(ls[1])
    max_walk_dist = eval(ls[2])
    depots = eval(ls[3])
    g = eval(ls[4])

problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)

vnames = ['student_stop_' + str(std_i) + '_' + str(stp_i)
          for std_i in range(len(students)) for stp_i in range(len(stops))] + \
    ["bus_edge_" + str(i) + "_" + str(v1) + "_" + str(v2)
     for i in depots for v1 in g for v2 in g]

vtypes = [problem.variables.type.binary
          for std_i in range(len(students)) for stp_i in range(len(stops))] + \
    [problem.variables.type.binary
     for i in depots for v1 in g for v2 in g]

vobj = [0
        for std_i in range(len(students)) for stp_i in range(len(stops))] + \
    [g[v1][v2]
     for i in depots for v1 in g for v2 in g]

problem.variables.add(obj=vobj,
                      lb=None,
                      ub=None,
                      types=vtypes,
                      names=vnames)

# Degree of bus depots
for b in depots:
    rhs = [1]
    sense = 'E'
    constraint = [
        ["bus_edge_" + str(b) + "_" + str(b) + "_" + str(v2) for v2 in g],
        [1 for v2 in g]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

    rhs = [0]
    sense = 'E'
    constraint = [
        ["bus_edge_" + str(b) + "_" + str(v2) + "_" + str(b) for v2 in g],
        [1 for v2 in g]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)
    for b2 in depots:
        if b2 != b:
            rhs = [0]
            sense = 'E'
            constraint = [
                ["bus_edge_" + str(b) + "_" + str(b2) + "_" + str(v2)
                 for v2 in g],
                [1 for v2 in g]
            ]
            # print(constraint)
            problem.linear_constraints.add(lin_expr=[constraint],
                                           senses=sense,
                                           rhs=rhs)

# Degree of school
rhs = [len(depots)]
sense = 'E'
constraint = [
    ["bus_edge_" + str(b) + "_" + str(v2) + "_" + str(0)
     for b in depots for v2 in g],
    [1 for b in depots for v2 in g]
]
problem.linear_constraints.add(lin_expr=[constraint],
                               senses=sense,
                               rhs=rhs)


rhs = [0]
sense = 'E'
constraint = [
    ["bus_edge_" + str(b) + "_" + str(0) + "_" + str(v2)
     for b in depots for v2 in g],
    [1 for b in depots for v2 in g]
]
problem.linear_constraints.add(lin_expr=[constraint],
                               senses=sense,
                               rhs=rhs)

# Degree of all the rest
for v in g:
    if v in depots + [0]:
        continue
    rhs = [1]
    sense = 'E'
    constraint = [
        ["bus_edge_" + str(b) + "_" + str(v) + "_" + str(v2)
         for b in depots for v2 in g],
        [1 for b in depots for v2 in g]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

    constraint = [
        ["bus_edge_" + str(b) + "_" + str(v2) + "_" + str(v)
         for b in depots for v2 in g],
        [1 for b in depots for v2 in g]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

    for b in depots:
        rhs = [0]
        sense = 'E'
        constraint = [
            ["bus_edge_" + str(b) + "_" + str(v) + "_" + str(v2) for v2 in g if v != v2] +
            ["bus_edge_" + str(b) + "_" + str(v2) + "_" + str(v)
             for v2 in g if v != v2],
            [1 for v2 in g if v != v2] + [-1 for v2 in g if v != v2]
        ]
        problem.linear_constraints.add(lin_expr=[constraint],
                                       senses=sense,
                                       rhs=rhs)

# 1-loops
for v in g:
    rhs = [0]
    sense = 'E'
    constraint = [
        ["bus_edge_" + str(b) + "_" + str(v) + "_" + str(v) for b in depots],
        [1 for b in depots]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

# All students go to a stop
for st_i in range(len(students)):
    rhs = [1]
    sense = 'E'
    constraint = [
        ['student_stop_' + str(st_i) + '_' + str(sp_i) for sp_i in range(len(stops))],
        [1 for sp_i in range(len(stops))]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

# If too far, student can't go to stop
for st_i in range(len(students)):
    for sp_i in range(len(stops)):
        if dist(stops[sp_i], students[st_i]) > max_walk_dist:
            rhs = [0]
            sense = 'E'
            constraint =[['student_stop_' + str(st_i) + '_' + str(sp_i)], [1]]
            problem.linear_constraints.add(lin_expr=[constraint],
                                           senses=sense,
                                           rhs=rhs)


class NoSeparateSubToursLazyConstraintCallback(cplex.callbacks.LazyConstraintCallback):

    def __call__(self):
        sols = self.get_values()
        gs = graphs(vnames, sols, depots, g)

        q = deque(depots)
        seen = []
        while len(q) > 0:
            v = q.popleft()
            seen.append(v)
            for i in range(len(depots)):
                q += gs[i][v]

        # print(seen)
        loops = [v for v in g if v not in seen]
        # print(loops)
        sloops = []
        pass

        while len(loops) > 0:
            q = deque([loops[0]])
            i = [i for i in range(len(depots)) if len(gs[i][loops[0]]) > 0][0]
            seen = []
            while len(q) > 0:
                v = q.popleft()
                seen.append(v)
                q += [v2 for v2 in gs[i][v] if v2 not in seen]
            sloops.append(seen)
            loops = [v for v in loops if v not in sloops[-1]]
        print(sloops)

        for loop in sloops:
            rhs = len(loop) - 1
            sense = 'L'
            constraint = [
                ["bus_edge_" + str(b) + "_" + str(v1) + "_" + str(v2)
                    for b in depots for v1 in loop for v2 in loop if v1 != v2],
                [1 for b in depots for v1 in loop for v2 in loop if v1 != v2]
            ]
            # print(rhs,constraint)
            self.add(constraint=constraint,
                     sense=sense,
                     rhs=rhs)


problem.register_callback(NoSeparateSubToursLazyConstraintCallback)
problem.solve()
print("BEST OBJ: ", problem.solution.get_objective_value())
sol = problem.solution.get_values()
# print(sol)
dsol = {vnames[i]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}
for k, v in dsol.items():
    print(k, v)
gs = graphs(vnames, sol, depots, g)

for g1 in gs:
    print(g1)
