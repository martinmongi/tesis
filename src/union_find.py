class UnionFind:
    def __init__(self,s):
        self.parent = {k:k for k in s}
        self.size = {k:1 for k in s}

    def find(self,x):
        while self.parent[x] != x:
            x, self.parent[x] = self.parent[x], self.parent[self.parent[x]]
        return x
    
    def union(self,x,y):
        xr = self.find(x)
        yr = self.find(y)

        if xr == yr:
            return
        
        if self.size[xr] < self.size[yr]:
            xr, yr = yr, xr
        
        self.parent[yr] = xr
        self.size[xr] += self.size[yr]
    
    def __repr__(self):
        return self.parent.__repr__()