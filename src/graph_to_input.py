from random import sample, choice, uniform
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
# vset = [(-58.36949853916, -34.6158134968029), (-58.3659405413778, -34.6226607079026), (-58.3667388080788, -34.6156239348096), (-58.3714220122462, -34.620671838114), (-58.3679754217283, -34.6251940332981), (-58.3739697954207, -34.6255566025354), (-58.3683153242606, -34.6216863014297), (-58.3691583824399, -34.6183731641986), (-58.3697563806587, -34.624159062634), (-58.3728541869498, -34.6207212188066), (-58.3745835005697, -34.6267595229402), (-58.3725528571228, -34.6266976921893), (-58.3670272395031, -34.6204845031196), (-58.371097541784, -34.6253682660577), (-58.3698017083908, -34.6171645791492), (-58.36972716474, -34.6252938414385), (-58.3664557513913, -34.6181188818719), (-58.3706622348626, -34.6294922755746), (-58.3663282018075, -34.6192436531565), (-58.3738829718558, -34.6267420385029), (-58.3709677445767, -34.6266457168852), (-58.3701565330508, -34.6184243024939), (-58.3772023870658, -34.6220650145937), (-58.3713367362319, -34.6218348155014), (-58.3740328449421, -34.6244350870638), (-58.3755547534025, -34.6233867429502), (-58.3717181969878, -34.6160242582574), (-58.3715205771077, -34.6195066168928), (-58.3730232125925, -34.6185027261175), (-58.3694619003706, -34.6165735363312), (-58.3684370188151, -34.6205961722389), (-58.3721011920138, -34.620288258754), (-58.3744426813242, -34.6172519220776), (-58.3757393169234, -34.6208294518232), (-58.3669021100186, -34.6215825860317), (-58.3665965504383, -34.6168777812925), (-58.372626678311, -34.6254779346272), (-58.3701009906641, -34.6165977589327), (-58.3695442246466, -34.6177510788319), (-58.3772718462442, -34.6197228530878)]
students = generate_students(S,vset,MAXW)
depots = sample(vset[1:], k=K)
# depots = [(-58.3738829718558, -34.6267420385029), (-58.3713367362319, -34.6218348155014)]

with open(options.out_file, 'w') as f:
    f.write(str(g) + '\n')
    f.write(str(vset) + '\n')
    f.write(str(students) + '\n')
    f.write(str(MAXW) + '\n')
    f.write(str(depots) + '\n')
    f.write(str(CAPACITY) + '\n')
