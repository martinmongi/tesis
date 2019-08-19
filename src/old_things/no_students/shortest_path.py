import random
import tikz
import cplex

with open('mann10.in', 'r') as f:
    ls = f.readlines()
    N = eval(ls[0])
    # print(N)
    g = eval(ls[1])

W = [N-1, (N-1)*10]
# print(g)



problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.minimize)
vnames = ["e_" + str(v1) + "_" + str(v2) for v1 in g for v2 in g[v1]]
vtypes = [problem.variables.type.binary for v1 in g for v2 in g[v1]]
vobj = [g[v1][v2] for v1 in g for v2 in g[v1]]
# print(vnames, vobj)

problem.variables.add(obj=vobj,
                      lb=None,
                      ub=None,
                      types=vtypes,
                      names=vnames)

# Grado de salida de 0 = 1
rhs = [2]
sense = 'E'
constraint = [
    ['e_0_' + str(v2) for v2 in g[0]],
    [1 for v2 in g[0]]
]
problem.linear_constraints.add(lin_expr=[constraint],
                               senses=sense,
                               rhs=rhs)

# Grado de entrada de 0 = 0
rhs = [0]
sense = 'E'
constraint = [
    ['e_' + str(v1) + '_' + str(v2)
     for v1 in g for v2 in g[v1] if v2 == 0],
    [1 for v2 in g[0]]
]
problem.linear_constraints.add(lin_expr=[constraint],
                               senses=sense,
                               rhs=rhs)

# Grado de entrada de  N*N-1 = 1
rhs = [2]
sense = 'E'
constraint = [
    ['e_' + str(v1) + '_' + str(v2)
     for v1 in g for v2 in g[v1] if v2 == N * N - 1],
    [1 for v2 in g[0]]
]
problem.linear_constraints.add(lin_expr=[constraint],
                               senses=sense,
                               rhs=rhs)

# Grado de salida de N*N-1 = 0
rhs = [0]
sense = 'E'
constraint = [
    ['e_' + str(N * N - 1) + '_' + str(v2) for v2 in g[N * N - 1]],
    [1 for v2 in g[0]]
]
problem.linear_constraints.add(lin_expr=[constraint],
                               senses=sense,
                               rhs=rhs)

# Grado de entrada = grado de salida
for v in range(1, N * N - 1):
    rhs = [0]
    sense = 'E'
    constraint = [
        ['e_' + str(v) + '_' + str(v2) for v2 in g[v]] +
        ['e_' + str(v2) + '_' + str(v) for v2 in g for v3 in g[v2] if v3 == v],
        [1 for v2 in g[v]] +
        [-1 for v2 in g for v3 in g[v2] if v3 == v],
    ]
    # print(v,constraint)
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)

for v in W:
    rhs = [1]
    sense = 'E'
    constraint = [
        ['e_' + str(v) + '_' + str(v2) for v2 in g[v]],
        [1 for v2 in g[v]]
    ]
    # print(v,constraint)
    problem.linear_constraints.add(lin_expr=[constraint],
                                   senses=sense,
                                   rhs=rhs)


class SubToursLazyConstraintCallback(cplex.callbacks.LazyConstraintCallback):

    def __call__(self):
        sol = self.get_values()
        dsol = {}
        for i in range(len(sol)):
            dsol[vnames[i]] = sol[i]

        for start_node in W:
            seen_nodes = [start_node]
            while True:
                for v2 in g[seen_nodes[-1]]:
                    if dsol['e_' + str(seen_nodes[-1]) + '_' + str(v2)] > .5:
                        seen_nodes.append(v2)
                        break
                print(seen_nodes, [k for k,v in dsol.items() if v > .5])
                if seen_nodes[-1] == N * N - 1 or seen_nodes[-1] in seen_nodes[:-1]:
                    break

            if seen_nodes[-1] in seen_nodes[:-1]:  # cycle
                seen_nodes = seen_nodes[:-1]
                print("Found subtour:", seen_nodes)
                rhs = len(seen_nodes) - 1
                sense = 'L'
                constraint = [
                    ['e_' + str(i) + '_' + str(j)
                        for i in seen_nodes for j in seen_nodes
                        if i != j and 'e_' + str(i) + '_' + str(j) in vnames],
                    [1 for i in seen_nodes for j in seen_nodes
                        if i != j and 'e_' + str(i) + '_' + str(j) in vnames]
                ]
                self.add(constraint=constraint,
                         sense=sense,
                         rhs=rhs)


problem.register_callback(SubToursLazyConstraintCallback)
problem.solve()
print("BEST OBJ: ", problem.solution.get_objective_value())
sol = problem.solution.get_values()
# print(sol)
dsol = {vnames[i]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}
for k,v in dsol.items():
    print(k,v)
