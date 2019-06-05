c = 0

for P in [10,20,40,80]:
    for S in [50,100,200,400,800]:
        for PG in [1,2,4,8,16]:
            for cap in [25,50]:
                if PG < P and cap*PG >= S:
                    print(P,S,PG,cap)
                    c+= 1
print(c)