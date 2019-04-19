from random import uniform, choices, triangular, choice
from utils import dist, mann_dist

STDN = 100
STPN = 20
MAXW = 2
DEPOTS = 4

stops = [(uniform(-10, 10), uniform(-10, 10)) for i in range(STPN)]
students = []
for i in range(STDN):

    st = choice(stops)

    while True:
        std = (uniform(st[0] - MAXW, st[0] + MAXW),
               uniform(st[1] - MAXW, st[1] + MAXW))
        # print(st,std)
        if dist(std,st) <= MAXW:
            break
    
    students.append(std)

g = {i: {} for i in range(STPN)}

for i in range(STPN):
    for j in range(STPN):
        g[i][j] = uniform(dist(stops[i], stops[j]),
                          mann_dist(stops[i], stops[j]))

print(stops)
print(students)
print(MAXW)
print(choices(range(1,STPN), k = DEPOTS))
print(g)
