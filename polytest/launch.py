import os, sys
import requests
import json
import spiral
from multiprocessing import Pool, Process, Queue, Lock, Manager, cpu_count
from subprocess import call

manager = Manager()
uniquepolygons = manager.list()
stuckpolygons = manager.list()
lock = Lock()


def invokeLambda(psList):
    global uniquepolygons
    try:
        r = requests.get("https://afexwi4dg8.execute-api.eu-west-3.amazonaws.com/api/polygon/%s"%(psList))
    
        try:
            pslistlov = [json.loads(lov)["vertex"] for lov in r.json()["result"]]
        
        except Exception:
            
            #print("Stuck!",r.json())
            return "!"

        for pslov in pslistlov:

            psreverse = pslov[:]
            psreverse.reverse()

            lock.acquire()
            
            if pslov not in uniquepolygons and psreverse not in uniquepolygons:
                
                if pslov < psreverse:
                    uniquepolygons.append(pslov)
                else:
                    pslov = psreverse
                    uniquepolygons.append(pslov)

                lock.release()

                return "*"

            lock.release()

            return "-"

    except Exception:
        #print("network error")
        return "x"

def writePolygonToFile(filename, polygon):
    path_to_filename = os.path.join("/tmp",filename)
    with open(path_to_filename, 'a') as dest_file:
        print(polygon.getJSON(), file=dest_file)

def vertexToList(num, vertexlist):

    for i in range(num):
        psList = []
        for v in vertexlist:
            psList.append(str(v[0]))
            psList.append(str(v[1]))
        yield ",".join(psList)

def vertexToOneStrList(vertexlist):
    psList = []
    for v in vertexlist:
        psList.append(str(v[0]))
        psList.append(str(v[1]))

    return ",".join(psList)

def mcLaunch(cycles, vertexlist):
    for i in range(cycles):
        psList= vertexToOneStrList(vertexlist)
        print(invokeLambda(psList))

def launch(cycles, vertexlist):

    num_cores = min(1, cpu_count() -1)
    pool = Pool(num_cores)
    
    for p in pool.imap_unordered(invokeLambda, vertexToList(cycles, vertexlist)):
        print(p,end='',flush=True)
    

if __name__=="__main__":

    cycles = 1000
    steps = 13
    g = spiral.Spiral(xzero=1,yzero=1)
    vertexlist = list(set(g.generate(steps=steps)))
    #vertexlist = [(0,0),(10,10),(10,0),(0,10),(5,6)]
    print("https://afexwi4dg8.execute-api.eu-west-3.amazonaws.com/api/polygon/%s"%(vertexToOneStrList(vertexlist)))

    launch(cycles, vertexlist)
    print("\n\n------------>\n\n",uniquepolygons,len(uniquepolygons))
    #mcLaunch(cycles, vertexlist)