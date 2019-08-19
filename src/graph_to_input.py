from random import sample, choice, uniform, shuffle
from utils import haversine_dist
from pprint import pprint
from optparse import OptionParser


def generate_students(n, stops, max_w):
    max_w_deg = max_w / 78710
    students = []
    for _ in range(n):
        st = choice(stops[1:])
        while True:
            std = (uniform(st[0] - max_w_deg, st[0] + max_w_deg),
                   uniform(st[1] - max_w_deg, st[1] + max_w_deg))
            if haversine_dist(std, st) <= max_w:
                break
        students.append(std)
    return students

parser = OptionParser()
parser.add_option("--if", dest="in_file")
parser.add_option("--of", dest="out_file")
parser.add_option("--N", "--stops", dest="N")
parser.add_option("--S", "--students", dest="S")
parser.add_option("--MAXW", "--max_walking_distance", dest="MAXW")
parser.add_option("--K", "--depots", dest="K")
parser.add_option("--C", "--capacity", dest="CAPACITY")
(options,args) = parser.parse_args()

N = int(options.N)
S = int(options.S)
MAXW = float(options.MAXW)
K = int(options.K)
CAPACITY = int(options.CAPACITY)

with open(options.in_file, 'r') as f:
    g = eval(f.readline())

vset = sample(list(g), k=N)
#Hardcoding vset
# vset = [(-58.3641982611742, -34.6329232148106), (-58.3705372376313, -34.6308083206452), (-58.3680808045065, -34.6479316448435), (-58.3632758388581, -34.6340426837291), (-58.3683246021838, -34.6353744081546), (-58.3679493413402, -34.6271409352361), (-58.3547379536006, -34.63663251928), (-58.3631826675481, -34.6289768533629), (-58.3650251618099, -34.6473259768234), (-58.3656703928655, -34.6273312471784), (-58.3594363198079, -34.6314507877897), (-58.359463516931, -34.6263749845397), (-58.3662473101925, -34.6341782921097), (-58.3637924602356, -34.6470653777426), (-58.3639102030837, -34.6284963166536), (-58.3617727544859, -34.6426397557631), (-58.3570779455599, -34.6356280918133), (-58.3580654409307, -34.6425639363932), (-58.3671988681114, -34.6427403503137), (-58.3664921721112, -34.6251939215099)]
students = generate_students(S,vset,MAXW)

depots = vset[1:]
shuffle(depots)
# Hardcoding depots
depots = depots[:K]
# depots = [(-58.3650251618099, -34.6473259768234), (-58.3705372376313, -34.6308083206452), (-58.3631826675481, -34.6289768533629), (-58.359463516931, -34.6263749845397)]
# depots = [(-58.3738829718558, -34.6267420385029), (-58.3713367362319, -34.6218348155014)]

with open(options.out_file, 'w') as f:
    f.write(str(g) + '\n')
    f.write(str(vset) + '\n')
    f.write(str(students) + '\n')
    f.write(str(MAXW) + '\n')
    f.write(str(depots) + '\n')
    f.write(str(CAPACITY) + '\n')
