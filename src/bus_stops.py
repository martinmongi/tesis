

import cplex
from collections import defaultdict, deque


def ralen(x):
    return range(len(x))


def reverse_graph(g):
    rg = defaultdict(lambda: {})
    for v in g:
        for v2 in g[v]:
            rg[v2][v] = g[v][v2]
    return rg


# INPUT
with open('easyloop.in', 'r') as f:
    ls = f.readlines()
    N = eval(ls[0])
    # print(N)
    g = eval(ls[1])
    rg = reverse_graph(g)
    W = eval(ls[2])
    bs = eval(ls[3])
    sp = eval(ls[4])


def graphs(vnames, vals):
    res = []
    dsol = {vnames[i]: vals[i] for i in ralen(vals)}
    for bn in ralen(bs):
        res.append(defaultdict(lambda: []))
        for v1 in g:
            for v2 in g[v1]:
                if dsol["busedge_" + str(bn) + "_" + str(v1) + "_" + str(v2)] > 0.5:
                    res[-1][v1].append(v2)
    return res


# START UP AND VARIABLES
problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)

vnames = ["busedge_" + str(i) + "_" + str(v1) + "_" + str(v2)
          for i in ralen(bs) for v1 in g for v2 in g[v1]] + \
    ["busvertexin_" + str(i) + "_" + str(v1) for i in ralen(bs) for v1 in g] + \
    ["busvertexout_" + str(i) + "_" + str(v1) for i in ralen(bs) for v1 in g] +\
    ["busstop_" + str(i) + "_" + str(v1) for i in ralen(bs) for v1 in g]

vtypes = [problem.variables.type.integer for i in ralen(bs) for v1 in g for v2 in g[v1]] + \
    [problem.variables.type.integer for i in ralen(bs) for v1 in g] + \
    [problem.variables.type.integer for i in ralen(bs) for v1 in g] + \
    [problem.variables.type.binary for i in ralen(bs) for v1 in g]

vobj = [g[v1][v2] for i in ralen(bs) for v1 in g for v2 in g[v1]] + \
    [0 for i in ralen(bs) for v1 in g] + \
    [0 for i in ralen(bs) for v1 in g] + \
    [0 for i in ralen(bs) for v1 in g]

vlb = [0 for i in ralen(bs) for v1 in g for v2 in g[v1]] + \
    [0 for i in ralen(bs) for v1 in g] + \
    [0 for i in ralen(bs) for v1 in g] + \
    [0 for i in ralen(bs) for v1 in g]

# print(vnames)

problem.variables.add(obj=vobj,
                      lb=vlb,
                      ub=None,
                      types=vtypes,
                      names=vnames)

# CONTSTRAINTS

# Degree constraints
for i in ralen(bs):
    for v in g:
        rhs = [0]
        sense = 'E'
        constraint = [
            ["busvertexout_" + str(i) + "_" + str(v)] +
            ["busedge_" + str(i) + "_" + str(v) + "_" + str(v2)
             for v2 in g[v]],
            [1] + [-1 for v2 in g[v]]
        ]
        problem.linear_constraints.add(lin_expr=[constraint],
                                       senses=sense,
                                       rhs=rhs)

        constraint = [
            ["busvertexin_" + str(i) + "_" + str(v)] +
            ["busedge_" + str(i) + "_" + str(v2) + "_" + str(v)
             for v2 in rg[v]],
            [1] + [-1 for v2 in rg[v]]
        ]
        problem.linear_constraints.add(lin_expr=[constraint],
                                       senses=sense,
                                       rhs=rhs)

        rhs = [0]
        sense = 'L'
        constraint = [
            ["busvertexout_" + str(i) + "_" + str(v),
             "busvertexin_" + str(i) + "_" + str(v),
             "busstop_" + str(i) + "_" + str(v)],
            [-1, -1, 1]
        ]
        problem.linear_constraints.add(lin_expr=[constraint],
                                       senses=sense,
                                       rhs=rhs)

        rhs = [0]
        sense = 'G'
        constraint = [
            ["busvertexout_" + str(i) + "_" + str(v),
             "busvertexin_" + str(i) + "_" + str(v),
             "busstop_" + str(i) + "_" + str(v)],
            [-1, -1, len(g)]
        ]
        problem.linear_constraints.add(lin_expr=[constraint],
                                       senses=sense,
                                       rhs=rhs)

# Para cada salida de bondi, el grado de salida del camino del bondi es 1
for i in ralen(bs):
    rhs = [1]
    sense = 'E'
    constraint = [
        ["busvertexout_" + str(i) + "_" + str(bs[i]),
         "busvertexin_" + str(i) + "_" + str(bs[i])],
        [1, -1]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs,
                                   names=['grado_salida_' + str(bs[i])])

# Grado de entrada de la escuela = 1, para todos los bondis
for i in ralen(bs):
    rhs = [-1]
    sense = 'E'
    constraint = [
        ["busvertexout_" + str(i) + "_" + str(sp),
         "busvertexin_" + str(i) + "_" + str(sp)],
        [1, -1]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

# Grado de entrada = Grado de salida
for i in ralen(bs):
    for v in g:
        if v == sp or v == bs[i]:
            continue
        rhs = [0]
        sense = 'E'
        constraint = [
            ["busvertexout_" + str(i) + "_" + str(v),
             "busvertexin_" + str(i) + "_" + str(v)],
            [1, -1]
        ]
        # print(v,constraint)
        problem.linear_constraints.add(lin_expr=[constraint],
                                       senses=sense,
                                       rhs=rhs)

# Un bondi pasa por alguno de
for v in W:
    rhs = [1]
    sense = 'E'
    constraint = [
        ["busstop_" + str(i) + "_" + str(v)],
        [1]
    ]
    # print(v,constraint)
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)


class NoSeparateSubToursLazyConstraintCallback(cplex.callbacks.LazyConstraintCallback):

    def __call__(self):
        sols = self.get_values()
        gs = graphs(vnames, sols)
        # print(gs)

        for bn in ralen(bs):
            gi = gs[bn]
            # print(gi)
            seen = [False for i in g]
            q = deque([bs[bn]])
            while len(q) > 0:
                v = q.popleft()
                seen[v] = True
                # print(v,gi[v])
                for v2 in gi[v]:
                    # print(v,v2)
                    if not seen[v2]:
                        q.append(v2)

            # print(bn, [i for i in gi.keys() if seen[i]],
            #         [i for i in gi.keys() if not seen[i]])

            cycles = [i for i in gi.keys() if not seen[i]]
            if len(cycles) > 0:
                for i in ralen(bs):
                    rhs = len(cycles) - 1
                    sense = 'L'
                    constraint = [
                        ["busstop_" + str(i) + "_" + str(v) for v in cycles] +
                        ["busedge_" + str(i) + "_" + str(v) + "_" + str(v2)
                         for v in cycles for v2 in g[v] if v2 not in cycles],
                        [1 for v in cycles] +
                        [-1 for v in cycles for v2 in g[v] if v2 not in cycles]
                    ]
                    # print(constraint,sense,rhs)
                    self.add(constraint=constraint,
                             sense=sense,
                             rhs=rhs)


problem.register_callback(NoSeparateSubToursLazyConstraintCallback)
problem.solve()
print("BEST OBJ: ", problem.solution.get_objective_value())
sol = problem.solution.get_values()
# print(sol)
dsol = {vnames[i]: sol[i] for i in ralen(sol) if sol[i] > 0.5}
for k, v in dsol.items():
    print(k, v)
gs = graphs(vnames, sol)

for g1 in gs:
    print(g1)
