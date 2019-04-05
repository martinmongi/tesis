import random

N = 30
W_size = int(N**1.5)

g = {i: {} for i in range(N * N)}


for i in range(N):
    for j in range(N):
        # derecha
        if j + 1 < N and random.choice([True]):
            g[i * N + j][i * N + j + 1] = random.random()
        # izquierda
        if j - 1 >= 0 and random.choice([True]):
            g[i * N + j][i * N + j - 1] = random.random()
        # abajo
        if i + 1 < N and random.choice([True]):
            g[i * N + j][(i + 1) * N + j] = random.random()
        # arriba
        if i - 1 >= 0 and random.choice([True]):
            g[i * N + j][(i - 1) * N + j] = random.random()

print(N)
print(g)
print(sorted(random.sample(range(0,N*N),W_size)))
print([0,N-1,N*(N-1),N*N-1])
print(int(N*N/2+ N/2))
