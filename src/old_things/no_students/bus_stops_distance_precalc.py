import cplex
from collections import defaultdict, deque
from heapq import *
from sys import argv


def reverse_graph(g):
    rg = defaultdict(lambda: {})
    for v in g:
        for v2 in g[v]:
            rg[v2][v] = g[v][v2]
    return rg


def heuristic_sbrp(g, bs, sp):
    paths = [[b] for b in bs]
    not_seen = set([v for v in g if v not in bs + [sp]])
    while len(not_seen) > 0:
        min_dist = float('inf')
        for path in paths:
            for v in not_seen:
                if g[path[-1]][v] < min_dist:
                    min_dist = g[path[-1]][v]
                    min_dist_pair = (path[-1], v)
        for path in paths:
            if min_dist_pair[0] == path[-1]:
                path.append(min_dist_pair[1])
                not_seen.remove(min_dist_pair[1])
    print(paths)

    onvars = []

    for path in paths:
        for i in range(len(path) - 1):
            onvars.append(
                "busedge_" + str(path[0]) + "_" + str(path[i]) + "_" + str(path[i + 1]))
        onvars.append(
            "busedge_" + str(path[0]) + "_" + str(path[-1]) + "_" + str(sp))

    varsnames = ["busedge_" + str(bn) + "_" + str(v1) + "_" + str(v2)
                 for bn in bs for v1 in g for v2 in g]
    varsvals = [1 if varsnames[i]
                in onvars else 0 for i in range(len(varsnames))]

    return [varsnames, varsvals]


# INPUT
with open(argv[1], 'r') as f:
    ls = f.readlines()
    N = eval(ls[0])
    # print(N)
    g = eval(ls[1])
    rg = reverse_graph(g)
    W = eval(ls[2])
    bs = eval(ls[3])
    sp = eval(ls[4])


dist = {}
vset = W + bs + [sp]

for vi in vset:
    dist[vi] = {v2: float('inf') for v2 in g}
    dist[vi][vi] = 0
    seen = [False for v in g]
    h = [(0, vi)]
    while len(h) > 0:
        v = heappop(h)[1]
        if seen[v]:
            continue
        seen[v] = True
        for v2 in g[v]:
            nd = dist[vi][v] + g[v][v2]
            if nd < dist[vi][v2]:
                dist[vi][v2] = nd
                heappush(h, (dist[vi][v2], v2))
    dist[vi] = {v: dist[vi][v] for v in dist[vi] if v in vset}
    # print(vi, dist[vi])


def graphs(vnames, vals):
    res = []
    dsol = {vnames[i]: vals[i] for i in range(len(vals))}
    for bn in bs:
        res.append(defaultdict(lambda: []))
        for v1 in dist:
            for v2 in dist[v1]:
                if dsol["busedge_" + str(bn) + "_" + str(v1) + "_" + str(v2)] > 0.5:
                    res[-1][v1].append(v2)
    return res


# START UP AND VARIABLES
problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)

vnames = ["busedge_" + str(i) + "_" + str(v1) + "_" + str(v2)
          for i in bs for v1 in vset for v2 in dist[v1]] + \
    ["buslength_" + str(b) for b in bs] + \
    ["busmaxlength"]

vtypes = [problem.variables.type.binary
          for i in bs for v1 in vset for v2 in dist[v1]] + \
    [problem.variables.type.continuous for b in bs] + \
    [problem.variables.type.continuous]

vobj1 = [dist[v1][v2] for i in bs for v1 in vset for v2 in dist[v1]] + \
    [0 for b in bs] + [0]

vobj2 = [0 for i in bs for v1 in vset for v2 in dist[v1]] + \
    [0 for b in bs] + [1]

problem.variables.add(obj=vobj1,
                      lb=None,
                      ub=None,
                      types=vtypes,
                      names=vnames)

# Bus lengths
for b in bs:
    rhs = [0]
    sense = 'E'
    constraint = [
        ["busedge_" + str(b) + "_" + str(v1) + "_" + str(v2)
         for v1 in vset for v2 in vset] +
        ["buslength_" + str(b)],
        [dist[v1][v2] for v1 in vset for v2 in vset] + [-1]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

    rhs = [0]
    sense = 'L'
    constraint = [
        ["buslength_" + str(b), "busmaxlength"],
        [1, -1]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)


# Degree of bus depots
for b in bs:
    rhs = [1]
    sense = 'E'
    constraint = [
        ["busedge_" + str(b) + "_" + str(b) + "_" + str(v2) for v2 in vset],
        [1 for v2 in vset]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

    rhs = [0]
    sense = 'E'
    constraint = [
        ["busedge_" + str(b) + "_" + str(v2) + "_" + str(b) for v2 in vset],
        [1 for v2 in vset]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)
    for b2 in bs:
        if b2 != b:
            rhs = [0]
            sense = 'E'
            constraint = [
                ["busedge_" + str(b) + "_" + str(b2) + "_" + str(v2)
                 for v2 in vset],
                [1 for v2 in vset]
            ]
            # print(constraint)
            problem.linear_constraints.add(lin_expr=[constraint],
                                           senses=sense,
                                           rhs=rhs)

# exit()

# Degree of school
rhs = [len(bs)]
sense = 'E'
constraint = [
    ["busedge_" + str(b) + "_" + str(v2) + "_" + str(sp)
     for b in bs for v2 in vset],
    [1 for b in bs for v2 in vset]
]
problem.linear_constraints.add(lin_expr=[constraint],
                               senses=sense,
                               rhs=rhs)


rhs = [0]
sense = 'E'
constraint = [
    ["busedge_" + str(b) + "_" + str(sp) + "_" + str(v2)
     for b in bs for v2 in vset],
    [1 for b in bs for v2 in vset]
]
problem.linear_constraints.add(lin_expr=[constraint],
                               senses=sense,
                               rhs=rhs)

# Degree of all the rest
for v in vset:
    if v in bs + [sp]:
        continue
    rhs = [1]
    sense = 'E'
    constraint = [
        ["busedge_" + str(b) + "_" + str(v) + "_" + str(v2)
         for b in bs for v2 in vset],
        [1 for b in bs for v2 in vset]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

    constraint = [
        ["busedge_" + str(b) + "_" + str(v2) + "_" + str(v)
         for b in bs for v2 in vset],
        [1 for b in bs for v2 in vset]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

    for b in bs:
        rhs = [0]
        sense = 'E'
        constraint = [
            ["busedge_" + str(b) + "_" + str(v) + "_" + str(v2) for v2 in vset if v != v2] +
            ["busedge_" + str(b) + "_" + str(v2) + "_" + str(v)
             for v2 in vset if v != v2],
            [1 for v2 in vset if v != v2] + [-1 for v2 in vset if v != v2]
        ]
        problem.linear_constraints.add(lin_expr=[constraint],
                                       senses=sense,
                                       rhs=rhs)


# 1-loops
for v in vset:
    rhs = [0]
    sense = 'E'
    constraint = [
        ["busedge_" + str(b) + "_" + str(v) + "_" + str(v) for b in bs],
        [1 for b in bs]
    ]
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

# 2-loops
# for v1 in vset:
#     for v2 in vset:
#         if v1 != v2:
#             rhs = [1]
#             sense = 'L'
#             constraint = [
#                 ["busedge_" + str(b) + "_" + str(v1) + "_" + str(v2) for b in bs] + \
#                 ["busedge_" + str(b) + "_" + str(v2) + "_" + str(v1) for b in bs],
#                 [1 for b in bs] + [1 for b in bs] 
#             ]
#             problem.linear_constraints.add(lin_expr=[constraint],
#                                         senses=sense,
#                                         rhs=rhs)


class NoSeparateSubToursLazyConstraintCallback(cplex.callbacks.LazyConstraintCallback):

    def __call__(self):
        sols = self.get_values()
        gs = graphs(vnames, sols)

        q = deque(bs)
        seen = []
        while len(q) > 0:
            v = q.popleft()
            seen.append(v)
            for i in range(len(bs)):
                q += gs[i][v]

        # print(seen)
        loops = [v for v in vset if v not in seen]
        # print(loops)
        sloops = []
        pass

        while len(loops) > 0:
            q = deque([loops[0]])
            i = [i for i in range(len(bs)) if len(gs[i][loops[0]]) > 0][0]
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
                ["busedge_" + str(b) + "_" + str(v1) + "_" + str(v2)
                    for b in bs for v1 in loop for v2 in loop if v1 != v2],
                [1 for b in bs for v1 in loop for v2 in loop if v1 != v2]
            ]
            # print(rhs,constraint)
            self.add(constraint=constraint,
                     sense=sense,
                     rhs=rhs)


problem.register_callback(NoSeparateSubToursLazyConstraintCallback)
problem.MIP_starts.add(heuristic_sbrp(dist, bs, sp),
                       problem.MIP_starts.effort_level.auto, "heur")
problem.solve()
print("BEST OBJ: ", problem.solution.get_objective_value())
sol = problem.solution.get_values()
# print(sol)
dsol = {vnames[i]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}
for k, v in dsol.items():
    print(k, v)
gs = graphs(vnames, sol)

for g1 in gs:
    print(g1)
