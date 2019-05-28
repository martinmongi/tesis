from utils import ProblemData
from random import sample
from collections import defaultdict
from pprint import pprint
from utils import vn


def greedy_stop_selection(stops, students, stop_to_students, capacity):
    res = defaultdict(lambda: tuple([]))
    uncovered = set(students)
    while len(uncovered) > 0:
        max_cover = (0, 0, tuple())
        for v in stops:
            cov = [s for s in stop_to_students[v] if s in uncovered][:capacity]
            if len(cov) > max_cover[0]:
                max_cover = (len(cov), v, tuple(cov))
        uncovered.difference_update(max_cover[2])
        res[max_cover[1]] = max_cover[2]
    print("CUBRIENDO", len(students), "CON", len(res), "PARADAS")
    return res


class InsertionHeuristic():
    def __init__(self, data):
        self.stops = greedy_stop_selection(
            data.stops, data.students, data.stop_to_students, data.capacity)
        unrouted = set(self.stops.keys())
        depots = [v for v in data.depots if v in self.stops]
        if len(depots) > 1.3 * len(data.students) / data.capacity:
            depots = sample(depots, int(
                1.2 * len(data.students) / data.capacity))
        elif len(depots) < 1.1 * len(data.students) / data.capacity:
            depots += sample([v for v in data.depots if v not in depots],
                             int(1.2 * len(data.students) / data.capacity) - len(depots))

        self.paths = [[v, data.school] for v in depots]
        self.load = [len(self.stops[v]) for v in depots]

        while len(unrouted) > 0:
            max_saving = (float('-inf'), 0, 0, 0)
            for v in unrouted:
                for path_i in range(len(self.paths)):
                    if self.load[path_i] + len(self.stops[v]) > data.capacity:
                        continue
                    for i in range(len(self.paths[path_i]) - 1):
                        vi = self.paths[path_i][i]
                        vj = self.paths[path_i][i + 1]
                        saving = data.dist[vi][vj] - \
                            data.dist[vi][v] - \
                            data.dist[v][vj]
                        if saving > max_saving[0]:
                            max_saving = (saving, v, path_i, i)
            _, v, path_i, i = max_saving
            self.paths[path_i] = self.paths[path_i][:i + 1] + [v] + self.paths[path_i][i + 1:]
            self.load[path_i] += len(self.stops[v])
            try:
                unrouted.remove(v)
            except KeyError:
                print("HEURISTIC FAILED")
                raise KeyError


def insertion_precalc_wrapper(data, vnames):
    try:
        heur = InsertionHeuristic(data)
    except KeyError:

        return
    onvars = []
    stop_route = {}
    for p in heur.paths:
        onvars.append(vn('RouteActive', data.v_index(p[0])))
        for i in range(len(p) - 1):
            onvars.append(vn('RouteEdge', data.v_index(p[0]),
                             data.v_index(p[i]), data.v_index(p[i+1])))
        for i in range(len(p)):
            onvars.append(vn('RouteStop', data.v_index(p[0]), data.v_index(p[i])))
            stop_route[p[i]] = p[0]

    for v in heur.stops:
        for s in heur.stops[v]:
            onvars.append(vn('RouteStopStudent', data.v_index(stop_route[v]),
                            data.v_index(v), data.s_index(s)))

    return (vnames, [1 if v in onvars else 0 for v in vnames])


def insertion_flat_wrapper(data, vnames):
    try:
        heur = InsertionHeuristic(data)
    except KeyError:
        return
    onvars = []
    stop_route = {}
    for p in heur.paths:
        onvars.append(vn('RouteActive', data.v_index(p[0])))
        for i in range(len(p) - 1):
            onvars.append(vn('Edge',
                             data.v_index(p[i]), data.v_index(p[i + 1])))
        for i in range(len(p)):
            onvars.append(
                vn('Stop', data.v_index(p[i])))
            stop_route[p[i]] = p[0]

    for v in heur.stops:
        for s in heur.stops[v]:
            onvars.append(vn('StopStudent',
                             data.v_index(v), data.s_index(s)))

    return (vnames, [1 if v in onvars else 0 for v in vnames])
