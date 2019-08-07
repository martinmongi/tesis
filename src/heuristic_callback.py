class NodeHeuristicCallback(cplex.callbacks.HeuristicCallback):
    def __call__(self):
        val_dict = {x[0][0]: x[1] for x in zip(variables, self.get_values())}
        # pprint(val_dict)
        stop_route = defaultdict(lambda: [])
        student_stop_route = defaultdict(lambda: [])
        edges_cost = defaultdict(lambda: defaultdict(lambda: {}))
        for vname in val_dict:
            sp = vname.split("_")
            if sp[0] == 'RouteStop':
                v0, s = map(int, sp[1:])
                stop_route[s].append((val_dict[vname], v0))
            if sp[0] == 'RouteStopStudent':
                v0, s, st = map(int, sp[1:])
                student_stop_route[st].append((val_dict[vname], v0, s))
            if sp[0] == 'RouteEdge':
                v0, s1, s2 = map(int, sp[1:])
                edges_cost[v0][s1][s2] = (1 - val_dict[vname]) * \
                    data.dist[data.vdictinv[s1]][data.vdictinv[s2]]

        for s in stop_route:
            shuffle(stop_route[s])
        for st in student_stop_route:
            shuffle(student_stop_route[st])
        # pprint(stop_route)
        # pprint(student_stop_route)

        onvars = set()
        stop_route_choice = {}
        routes = defaultdict(lambda: {})
        for s in stop_route:
            highest = 0.0
            best = None
            for val, v0 in stop_route[s]:
                if val > highest:
                    highest = val
                    best = v0
            stop_route_choice[s] = best
            if best is not None:
                onvars.add(vn('RouteStop', best, s))
                onvars.add(vn('RouteActive', best))
                routes[best][s] = None
        # pprint(stop_route_choice)

        student_stop_route_choice = {}
        for st in student_stop_route:
            highest = 0.0
            for val, v0, s in student_stop_route[st]:
                if val > highest and stop_route_choice[s] == v0:
                    highest = val
                    best = v0, s
            student_stop_route_choice[st] = best
            onvars.add(vn('RouteStopStudent', best[0], best[1], st))
        # pprint(student_stop_route_choice)
        # pprint(onvars)

        # pprint(route_edges)
        school = data.v_index(data.school)
        for v0 in edges_cost:
            routes[v0][v0] = school
            # print(routes[v0])
            out_of_tour = set(routes[v0].keys())
            out_of_tour.difference_update([v0])
            # print(out_of_tour)

            while len(out_of_tour) > 0:
                best = (float('+inf'), 0, 0)
                for v in out_of_tour:
                    vi = v0
                    while vi != school:
                        vnext = routes[v0][vi]
                        new_cost = (
                            edges_cost[v0][vi][v] + edges_cost[v0][v][vnext] -
                            edges_cost[v0][v][vnext],
                            vi, v)
                        # print(new_cost)
                        best = min(best, new_cost)
                        vi = routes[v0][vi]
                # print(best)
                _, vi, v = best
                vnext = routes[v0][vi]
                # print("AGREGO", v, "DESPUES DE", vi, "ANTES DE", vnext)
                routes[v0][v] = vnext
                routes[v0][vi] = v
                out_of_tour.remove(v)
            for k, v in routes[v0].items():
                onvars.add(vn("RouteEdge", v0, k, v))
            # print(routes[v0])

        res = [[v[0] for v in variables], [
            1 if v[0] in onvars else 0 for v in variables]]
        self.set_solution(res)


# problem.register_callback(NodeHeuristicCallback)
