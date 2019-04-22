import matplotlib.pyplot as plt
from sys import argv

with open(argv[1], 'r') as f:
    ls = f.readlines()
    stops = eval(ls[0])
    students = eval(ls[1])
    max_walk_dist = eval(ls[2])
    depots = eval(ls[3])
    g = eval(ls[4])

plt.plot([stops[0][0]], [stops[0][1]], 'gs')
plt.plot([stops[dep][0] for dep in depots],
         [stops[dep][1] for dep in depots], 'y^')
plt.plot([stops[i][0] for i in range(1,len(stops)) if i not in depots],
         [stops[i][1] for i in range(1,len(stops)) if i not in depots], 'ro')
plt.plot([s[0] for s in students], [s[1] for s in students], 'bx')

if len(argv) > 2:
    with open(argv[2], 'r') as f:
        ls = f.readlines()
        # for i in range(len(depots)):
        g = eval(ls[0])
        for v, v2 in g.items():
            v2 = v2[0]
            plt.plot([stops[v][0], stops[v2][0]],
                        [stops[v][1], stops[v2][1]])
        stdict = eval(ls[-1])
        for k, v in stdict.items():
            # plt.plot([students[k][0], stops[v][0]], [students[k][1], stops[v][1]])
            pass
plt.show()
