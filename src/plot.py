from optparse import OptionParser
from utils import transpose, ProblemData
from pprint import pprint
from sys import argv
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

parser = OptionParser()
parser.add_option("--graph", dest="graph")
parser.add_option("--if", dest="in_file")
parser.add_option("--of", dest="out_file")
(options, args) = parser.parse_args()

COLORS = ['c', 'm', 'y', 'r', 'g', 'b', 'k']

plt.figure(figsize=(10,10))

if options.graph:
    with open(options.graph, 'r') as f:
        g = eval(f.readline())
        for v in g:
            for v2 in g[v]:
                path = g[v][v2][1]
                plt.plot([p[0] * 1000 for p in path],
                        [p[1] * 1000 for p in path], '-', color='0.95')
                plt.arrow(path[-2][0] * 1000,
                        path[-2][1] * 1000,
                        (path[-1][0] - path[-2][0]) * 1000 / 2,
                        (path[-1][1] - path[-2][1]) * 1000 / 2, head_width=.2, head_length=.2, color='0.95')
        plt.xticks([])
        plt.yticks([])

data = ProblemData(options.in_file)
plt.plot([s[0] * 1000 for s in data.students], \
    [s[1] * 1000 for s in data.students], 'b.', label="Estudiantes")

if options.out_file:
    with open(options.out_file, 'r') as f:
        ls = f.readlines()
        assignment = eval(ls[-1])
        for st, s in assignment.items():
            # if len(data.student_to_stop[st]) > 1:
            # plt.plot([p[0] * 1000 for p in [st, s]],
            #         [p[1] * 1000 for p in [st, s]], color='b', ls='--')
            pass
        for i in range(len(ls) - 1):
            g = eval(ls[i])
            for v1 in g:
                for v2 in g[v1]:
                    # plt.plot([p[0] * 1000 for p in g[v1][v2]],
                    #          [p[1] * 1000 for p in g[v1][v2]],
                    #          color=COLORS[i % len(COLORS)])
                    plt.plot([g[v1][v2][0][0] * 1000, g[v1][v2][-1][0] * 1000],
                             [g[v1][v2][0][1] * 1000, g[v1][v2][-1][1] * 1000],
                             color=COLORS[i % len(COLORS)])

plt.plot([data.stops[0][0] * 1000],
            [data.stops[0][1] * 1000], 'gh', markersize=10, label="Escuela")
plt.plot([dep[0] * 1000 for dep in data.depots],
            [dep[1] * 1000 for dep in data.depots], 'g^', markersize=10, label="Garages")
plt.plot([s[0] * 1000 for s in data.stops[1:] if s not in data.depots],
            [s[1] * 1000 for s in data.stops[1:] if s not in data.depots], 'ro', label="Paradas")
plt.legend()

fn=options.out_file if options.out_file else (
    options.in_file if options.in_file else options.graph)
# plt.show()
plt.savefig(fn + '.pdf', bbox_inches='tight')
