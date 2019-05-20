from random import uniform, choices, triangular, choice, sample
from utils import distance, generate_students

STDN = 10
STPN = 3
MAXW = 1
DEPOTS = 1
CAPACITY = 10

with open(str(STDN) + '_' + str(STPN) + '_' + str(MAXW) + '_' + str(DEPOTS) + '_' + str(CAPACITY) + '.in', 'w') as f:

    stops = [(uniform(-10, 10), uniform(-10, 10)) for i in range(STPN)]
    g = {i: {} for i in range(STPN)}

    for i in range(STPN):
        for j in range(STPN):
            g[i][j] = dist(stops[i], stops[j])

    students = generate_students(STDN, stops, MAXW)
    
    f.write(str(stops) + '\n')
    f.write(str(students) + '\n')
    f.write(str(MAXW) + '\n')
    f.write(str(sample(range(1, STPN), k=DEPOTS)) + '\n')
    f.write(str(CAPACITY) + '\n')
    f.write(str(g) + '\n')
