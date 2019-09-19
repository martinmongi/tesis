
import subprocess

instances = [
    (barrio, n, estu, buses, cap, maxw)
    for barrio in ["barracas", "boca"]
    for n in [15,25,35]
    for estu,buses in [(100,2),(200,4),(300,6)]
    for cap in [60]
    for maxw in [200]
]

for neig, stops, studs, buses, cap, maxw in instances:
    print(neig, stops, studs, buses, "x", cap,  maxw)
    subprocess.run(["python", ".\\graph_to_input.py", "--if", ".\data\\" + neig + ".g", "--S",
                    str(studs), "--K", str(buses), "--C", str(cap), "--N", str(stops), "--MAXW", str(maxw), "--hardcode", neig])