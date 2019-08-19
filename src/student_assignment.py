import cplex
from utils import vn, haversine_dist
from pprint import pprint


def assign_students_mip(data, gs):

    vset = set()
    for v0 in gs:
        vset.update(gs[v0].keys())

    problem = cplex.Cplex()
    problem.objective.set_sense(problem.objective.sense.minimize)
    problem.set_log_stream(None)
    problem.set_error_stream(None)
    problem.set_warning_stream(None)
    problem.set_results_stream(None)

    variables = [(vn('StopStudent', data.v_index(v1), data.s_index(s)), 'B', haversine_dist(s,v1))
                 for s in data.students for v1 in data.student_to_stop[s] if v1 in vset]

    problem.variables.add(obj=[v[2] for v in variables],
                          types=[v[1] for v in variables],
                          names=[v[0] for v in variables])

    # for s in data.students:
    #     print(data.s_index(s), list(map(data.v_index, data.student_to_stop[s])))
    # Choice adds to one
    rhs = [1 for s in data.students]
    sense = ['E' for s in data.students]
    constraint = [[
        [vn('StopStudent', data.v_index(v1), data.s_index(s))
            for v1 in data.student_to_stop[s] if v1 in vset],
        [1 for v1 in data.student_to_stop[s] if v1 in vset]
    ]for s in data.students]
    # pprint(constraint)
    names = ['choice_addition_' + str(data.s_index(s)) for s in data.students]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs, names=names)

    # Capacities are respected
    rhs = [data.capacity for v0 in gs]
    sense = ['L' for v0 in gs]
    constraint = [[
        [vn('StopStudent', data.v_index(v), data.s_index(s))
            for v in gs[v0] if v in data.stops for s in data.stop_to_students[v]],
        [1 for v in gs[v0] if v in data.stops for s in data.stop_to_students[v]]
    ] for v0 in gs]
    problem.linear_constraints.add(lin_expr=constraint, senses=sense, rhs=rhs)

    problem.solve()
    print("BEST STUDENT ASSIGNMENT WALKING DISTANCE: ", problem.solution.get_objective_value())

    sol = problem.solution.get_values()
    dsol = {variables[i][0]: sol[i] for i in range(len(sol)) if sol[i] > 0.5}
    assignment = {}
    for vname in dsol:
        if dsol[vname] < 0.5:
            continue
        sp = vname.split("_")
        if sp[0] == 'StopStudent':
            v, s = map(int, sp[1:])
            assignment[data.students[s]] = data.vdictinv[v]
    return assignment

