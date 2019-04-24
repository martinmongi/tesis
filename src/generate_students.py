from random import uniform, choices, triangular, choice, sample
from utils import dist, mann_dist

STDN = 100
STPN = 20
MAXW = 1
DEPOTS = 3
CAPACITY = 35

with open('input/' + str(STDN) + '_' + str(STPN) + '_' + str(MAXW) + '_' + str(DEPOTS) + '_' + str(CAPACITY) + '.in', 'w') as f:

    stops = [(uniform(-10, 10), uniform(-10, 10)) for i in range(STPN)]
    students = []
    for i in range(STDN):
        st = choice(stops[1:])
        while True:
            std = (uniform(st[0] - MAXW, st[0] + MAXW),
                   uniform(st[1] - MAXW, st[1] + MAXW))
            # print(st,std)
            if dist(std, st) <= MAXW:
                break
        students.append(std)

    g = {i: {} for i in range(STPN)}

    for i in range(STPN):
        for j in range(STPN):
            g[i][j] = uniform(dist(stops[i], stops[j]),
                              dist(stops[i], stops[j]))

    f.write(str(stops) + '\n')
    f.write(str(students) + '\n')
    f.write(str(MAXW) + '\n')
    f.write(str(sample(range(1, STPN), k=DEPOTS)) + '\n')
    f.write(str(CAPACITY) + '\n')
    f.write(str(g) + '\n')
