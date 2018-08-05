from chalice import Chalice

import sys
import os
import time
import random
import time
import hashlib
import json
import itertools
from math import sqrt
from os import system
from collections import Counter, defaultdict
from copy import deepcopy
from random import randint, sample, choice

import networkx as nx

class AdjacentMatrix:

    def __init__(self, list_of_points):
        self.dimension = len(list_of_points)
        self.list_of_points = list_of_points
        self.adjmatrix = self.generateMatrix()


    def getSegments(self):
        return nx.edges(self.adjmatrix)

    def getSegmentsForAVertex(self,v):
        return list(self.adjmatrix.edges(v))

    def generateMatrix(self, diagonal=False):

        matrix = nx.Graph()
        matrix.add_nodes_from(range(self.dimension))
        matrix.add_edges_from([(i,j) for i in range(self.dimension) for j in range(self.dimension) if i!=j])

        return matrix

    def addSegment(self, p, q):
        self.adjmatrix.add_edge(p,q)

    def removeSegments(self, numofsegments):
        for i in range(numofsegments):
            n = nx.number_of_edges(self.adjmatrix)
            pos = random.randint(0,n-1)
            segmentToBeRemoved = list(self.adjmatrix.edges)[pos]
            self.adjmatrix.remove_edges_from([segmentToBeRemoved])

    def removeSegment(self, p, q):
        try:
            self.adjmatrix.remove_edge(p,q)
        except:
            pass #edge already removed


    def getConnectedComponents(self):
        d = list(nx.connected_component_subgraphs(self.adjmatrix))
        return d

    def getNumberConnectedComponents(self):
        d = list(nx.connected_component_subgraphs(self.adjmatrix))

        return len(d)

    def __repr__(self):
        return str(self.adjmatrix)



def onSegment(p, q, r):
    if (q[0] < max(p[0], r[0]) and q[0] > min(p[0], r[0]) and \
        q[1] < max(p[1], r[1]) and q[1] > min(p[1], r[1])):
        return True
    return False

def orientation(p, q, r):

    val = (q[1] - p[1]) * (r[0] - q[0]) -\
    (q[0] - p[0]) * (r[1] - q[1])

    if val == 0:
        return 0
    if val > 0:
        return 1
    else:
        return 2

def pointBelongsToSegment(a, b, c):

    crossproduct = (c[1] - a[1]) * (b[0] - a[0]) - (c[0] - a[0]) * (b[1] - a[1])

    # compare versus epsilon for floating point values, or != 0 if using integers
    if abs(crossproduct) != 0:
        return False

    dotproduct = (c[0] - a[0]) * (b[0] - a[0]) + (c[1] - a[1])*(b[1] - a[1])
    if dotproduct < 0:
        return False

    squaredlengthba = (b[0] - a[0])*(b[0] - a[0]) + (b[1] - a[1])*(b[1] - a[1])
    if dotproduct > squaredlengthba:
        return False

    return True

def doIntersect(p1, q1, p2, q2):

    # Shared points

    if p1==p2 or p1==q2:
        return False
    if q1==p2 or q1==q2:
        return False

#    Points belong to other line
    
    # a = p1[1]-p2[1]
    # b = (q2[1]-p2[1])*(p1[0]-p2[0])/(q2[0]-p2[0])
    
    # c = q1[1]-p2[1]
    # d = (q2[1]-p2[1])*(q1[0]-p2[0])/(q2[0]-p2[0])
    
    # e = p2[1]-p1[1]
    # f = (q1[1]-p1[1])*(p2[0]-p1[0])/(q1[0]-p1[0])
    
    # g = q2[1]-p1[1]
    # h = (q1[1]-p1[1])*(q2[0]-p1[0])/(q1[0]-p1[0])

    
    # if a==b or c==d:
    #     return False
    # if e==f or g==h:
    #     return False

    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    if (o1 != o2 and o3 != o4):
        #print("I 0")
        return True

    if (o1 == 0 and onSegment(p1, p2, q1)):
#        print("I 1")
#        print("->",p1,p2,q1)
        return True

    if (o2 == 0 and onSegment(p1, q2, q1)):
#        print("I 2")
#        print("->",p1,q2,q1)
        return True

    if (o3 == 0 and onSegment(p2, p1, q2)):
#        print("I 3")
#        print("->",p2,p1,q2)
        return True

    if (o4 == 0 and onSegment(p2, q1, q2)):
#        print("I 4")
#        print("->",p2,q1,q2)
        return True

    #print("PASS")
    return False

class PolygonStruct:

    def __init__(self, listofpoints):
        listofpoints.sort()
        self.listofpoints = listofpoints

        self.initialvertex = listofpoints[0]
        self.lop = {val:{"i":listofpoints.index(val),"v":val} for val in listofpoints}
        self.loi = {listofpoints.index(val):{"i":listofpoints.index(val),"v":val} for val in listofpoints}

        self.size = len(listofpoints)
        self.lov = []

        self.am = AdjacentMatrix(listofpoints)
        self.oldadjmatrix = deepcopy(self.am.adjmatrix)
        self.lastnodesegments = []
        self.firstnodesegments = []
        self.nvnodesegments = []
        self.qnodesegments = []

        self.cycleinfo = {"subgraphs":0, "threeone":0,"unreachable":0, "firstnodeisolated":0}
        self.currentdeadends = []
        self.stuck = False

        self.intersectmatrix = {}
    

    def generateIntersectMatrix(self):

        combinations = list(itertools.combinations(range(self.size),2))
        for c in combinations:
            self.intersectmatrix[c] = []
        for k,v in self.intersectmatrix.items():
            for otherpairofvertex in self.intersectmatrix:
                p = self.loi[k[0]]["v"]
                q = self.loi[k[1]]["v"]
                r = self.loi[otherpairofvertex[0]]["v"]
                s = self.loi[otherpairofvertex[1]]["v"]
                if doIntersect(p,q,r,s):
                    self.intersectmatrix[k].append(otherpairofvertex)



    def area(self):
        area = float(0)
        j = len(self.lov)-2
        X = [p[0] for p in self.lov[:-1]]
        Y = [p[1] for p in self.lov[:-1]]
    
        for i in range(len(self.lov)-1):
            area += (X[j]+X[i]) * (Y[j]-Y[i])
            j=i
        return abs(area/2)

    def perimeter(self):

        peri = float(0)
        for i in range(len(self.lov)-1):
            a = self.lov[i]
            b = self.lov[+1]
            peri+= sqrt(abs(a[0]-b[0])+abs(a[1]-b[1]))
        return peri

    def hash(self):
        h = hashlib.sha256()
        encodedlov = str(self.lov).encode()
        h.update(encodedlov)
        return h.hexdigest()

    def getJSON(self):
        vertex = [list(elem) for elem in self.lov]
        peri = self.perimeter()
        area = self.area()
        polyhash = self.hash()
        jsonvertex = {"vertex":vertex, "hash":polyhash, "properties": {"perimeter":peri, "area":area}}
        return json.dumps(jsonvertex)

    def getDict(self):
        vertex = [elem for elem in self.lov]
        peri = self.perimeter()
        area = self.area()
        polyhash = self.hash()
        jsonvertex = {"vertex":vertex, "hash":polyhash, "properties": {"perimeter":peri, "area":area}}
        return jsonvertex


    def reset(self):

        self.lov = []
        self.setInitialVertex()
        self.am = AdjacentMatrix(self.listofpoints)
        self.oldadjmatrix = deepcopy(self.am.adjmatrix)
        self.lastnodesegments = []
        self.firstnodesegments = []
        self.nvnodesegments = []
        self.qnodesegments = []



    def traceback(self):
        print("---------------------------")
        print("LOP",self.lop.keys())
        print("am",self.am)
        print("isolatedparts",self.getIsolatedParts())
        print("isolatedparts",self.getIsolatedPartsAsListsOfPoints())
        print("LEN isolatedparts",len(self.getIsolatedPartsAsListsOfPoints()[0]))

        print("firstnodesegments",self.firstnodesegments)
        print("qnodesegments",self.qnodesegments)
        print("nvnodesegments",self.nvnodesegments)
        print("checkIsolatedGraphs",self.checkIsolatedGraphs())
        print("unreachable",self.checkUnreachableOneNeighborNodes())
        print("threeone",self.checkThreeOneNeighborNodes())

        print("---------------------------")

    def setInitialVertex(self):

        self.lov.append(self.initialvertex)
        self.removeSuperimposingEdges()


    def removeSuperimposingEdges(self):

        edgestoberemoved = []
        for point in self.listofpoints:
            for edge in self.am.getSegments():
                c = point
                a = self.loi[edge[0]]["v"]
                b = self.loi[edge[1]]["v"]
                if pointBelongsToSegment(a,b,c):
                    if c not in [a,b]:
                        edgestoberemoved.append(edge)
        self.am.adjmatrix.remove_edges_from(edgestoberemoved)
    
        self.oldadjmatrix = deepcopy(self.am.adjmatrix)

    def allPointsUsed(self):

        return len(self.lov) == len(self.lop)

    def rebuildTemporaryPolygon(self, listofvertex):
        self.lov = []
        listofpoints = list(self.lop.keys())
        listofpoints.sort()
        self.am = AdjacentMatrix(listofpoints)
        self.oldadjmatrix = deepcopy(self.am.adjmatrix)
        self.setInitialVertex()
        for v in listofvertex:
            self.forcedCycle(v)

    def checkValidFinalPolygon(self):

        if not self.allPointsUsed():
            return False
        lovtest = self.lov[:]
        lovtest.append(self.lov[0])
        p = lovtest[-2]
        q = lovtest[-1]

        try:
            for i in range(self.size):
                r = lovtest[i]
                s = lovtest[i+1]
                if doIntersect(p,q,r,s):
                    return False
        except:
            False
        return True


    def chooseVertex(self, vpos, segments):

        try:
            availablesegments = list(set(segments) - set(self.currentdeadends))
            #print("AVSEG",availablesegments)
            segmentstoberemoved = []
            for avseg in availablesegments:
                for avsegpot in availablesegments:
                    if avseg != avsegpot:
                        a = self.loi[avseg[0]]["v"]
                        b = self.loi[avseg[1]]["v"]
                        c = self.loi[avsegpot[1]]["v"]
                        if pointBelongsToSegment(a,b,c):
                            #print("ABC",a,b,c)
                            segmentstoberemoved.append(avseg)
            availablesegments = list(set(availablesegments) - set(segmentstoberemoved))
            #print("availablesegments",availablesegments)
            ch = choice(availablesegments)
            # if ch[0] != vpos:
            #     vertex = self.loi[ch[0]]["v"]
            #     print("CUIDADO!")
            vertex = self.loi[ch[1]]["v"]
            return vertex
        except:
            return None

    def tryNewVertex(self):

        if len(self.lov) == 1:
            #print("iniciamos")
            currentvertex = self.lov[0]
            qpos = self.lop[currentvertex]["i"]
            segments = self.am.getSegmentsForAVertex(qpos)
            chosenvertex = self.chooseVertex(qpos, segments)
            #print("elegimos el segundo vertice",chosenvertex)
            return chosenvertex

        #print("otro vertice")
        currentvertex = self.lov[-1]
        previousvertex = self.lov[-2]
        #print("current vertex",currentvertex)
        qpos = self.lop[currentvertex]["i"]
        qminusonepos = self.lop[previousvertex]["i"]
        self.am.removeSegment(qpos,qminusonepos) #to avoid going back
        segments = self.am.getSegmentsForAVertex(qpos)
        self.am.addSegment(qpos,qminusonepos) #restore connection
        #print("segments",segments)
        chosenvertex = self.chooseVertex(qpos, segments)
        return chosenvertex


    def setNewSegment(self, point):
        #print("new vertex to try",point)
        vpos = self.lop[point]["i"]
        vprev = self.lop[self.lov[-1]]["i"]
        self.am.removeSegment(vpos,vprev) #to avoid going back

        return point

    def rebuildLOVGraph(self):
        for i in range(len(self.lov)-1):
             v = self.lov[i]
             vplus = self.lov[i+1]
             inode = self.lop[v]["i"]
             inodeplus = self.lop[vplus]["i"]
             self.am.adjmatrix.add_edge(inode,inodeplus)
        

    def removeSegment(self, p, q):
        pnode = self.lop[p]["i"]
        qnode = self.lop[q]["i"]
        self.am.removeSegment(pnode,qnode)

    def removenodesegments(self, v):

        vnode = self.lop[v]["i"]
        vnodesegments = self.am.getSegmentsForAVertex(vnode)
        self.am.adjmatrix.remove_edges_from(vnodesegments)
        return vnodesegments

    def addnodesegments(self, segments):

        self.am.adjmatrix.add_edges_from(segments)

    def getSubGraphsWithNoInitialVertex(self):
        sgwoiv = []
        subgraphs = self.am.getConnectedComponents()
        for sg in subgraphs:
            try:
                sg[self.lop[self.initialvertex]["i"]]
            except:
                sgwoiv.append(sg)
        return sgwoiv

    def getSubGraphWithNoInitialVertex(self):
        if self.numberofisolatedparts == 1:
            return None
        subgraphs = self.am.getConnectedComponents()
        for sg in subgraphs:
            try:
                sg[self.lop[self.initialvertex]["i"]]
            except:
                return sg

    def checkThreeOneNeighborNodes(self):

        graph = self.getSubGraphWithNoInitialVertex()
        if not graph:
            return True
        edges = graph.edges
        nodesA = [i[0] for i in edges]
        nodesB = [i[1] for i in edges]
        j=Counter(nodesA+nodesB)
        numberofones = list(j.values()).count(1)
        #print("number of 1-neighbor nodes",numberofones)
        if numberofones > 2:
            return False
        return True


    def checkIsolatedGraphs(self, maxnumber=2):

        if self.numberofisolatedparts() > maxnumber: #something's wrong here
            #print("max number of isolated parts exceeded",self.numberofisolatedparts())
            return False
        return True

    def selfintersect(self):
        lovsize = range(len(self.lov)-1)
        for i in lovsize:
            p = self.lov[i]
            q = self.lov[i+1]
            for j in lovsize:
                r = self.lov[j]
                s = self.lov[j+1]
                if doIntersect(p,q,r,s):
                    self.am.adjmatrix = self.oldadjmatrix
                    self.lov.pop()
                    #print("SELFINTERSECT")
                    time.sleep(1)
                    return False
        return True





    def checkUnreachableOneNeighborNodes(self):
        graph = self.getSubGraphWithNoInitialVertex()
        if not graph:
            return True
        edges = graph.edges
        nodesA = [i[0] for i in edges]
        nodesB = [i[1] for i in edges]
        j=Counter(nodesA+nodesB)
        oneNeighborNodes = []
        for i in j:
            if j[i] == 1:
                oneNeighborNodes.append(self.loi[i]["v"])

        p = self.initialvertex
        q = self.lov[-1]
        pIntersect = False
        qIntersect = False
        nIntersects ={}
        for i in range(len(self.lov)-1):
            r = self.lov[i]
            s = self.lov[i+1]
            for n in oneNeighborNodes:
                nIntersects[n] = {"q":False,"p":False}
                #print("testing ONE",n)
                if doIntersect(p,n,r,s):
                    nIntersects[n]["p"] = True
                    pIntersect = True
                if doIntersect(q,n,r,s):
                    nIntersects[n]["q"] = True
                    qIntersect = True
        if len(oneNeighborNodes) == 1:
            if pIntersect and qIntersect:
                #print("Intersectamos con ambos")
                return False
        #print("nIntersects",nIntersects)
        if len(oneNeighborNodes) == 2:
            for n in nIntersects:
                if nIntersects[n]["p"] and nIntersects[n]["q"]:
                    return False
            pIsolated = True
            qIsolated = True
            for n in nIntersects:
                if not nIntersects[n]["p"]:
                    pIsolated = False
                if not nIntersects[n]["q"]:
                    qIsolated = False
            if pIsolated or qIsolated:
                return False
        return True

    def forcedCycle(self,point):
        self.cycle(point, verbose=True)


    def cycle(self, point=None, verbose=False):

        if not point:
            nv = self.tryNewVertex()
        else:
            nv = point

        if nv:
            p = self.lov[0]
            q = self.lov[-1]

            self.lov.append(nv)

            self.oldadjmatrix = deepcopy(self.am.adjmatrix) # copy so we can backtrack
            #print("ACABAMOS DE BORRAR",self.firstnodesegments)

            if len(self.lov) < self.size:

                self.removeIntersectSegments(q,nv)
                self.am.removeSegment(0,self.lop[nv]["i"])        

                self.firstnodesegments = self.removenodesegments(self.initialvertex)
               # print("SFN",self.firstnodesegments)
                self.qnodesegments = self.removenodesegments(q)
                self.nvnodesegments = self.removenodesegments(nv)


                self.rebuildLOVGraph()

           
                if len(self.firstnodesegments) > 1:
                 if self.checkIsolatedGraphs():
                    if self.checkUnreachableOneNeighborNodes():
                        if self.checkThreeOneNeighborNodes():
                            self.addnodesegments(self.nvnodesegments)

                            self.addnodesegments(self.firstnodesegments)
                        # self.removeIntersectSegments(q,nv,self.firstnodesegments)

                        

                            self.currentdeadends = []

                        else:
                            self.cycleinfo["threeone"] +=1
                            self.undoLastVertex()
                    else:
                        self.cycleinfo["unreachable"] +=1
                        self.undoLastVertex()
                 else:
                    self.cycleinfo["subgraphs"] +=1
                    self.undoLastVertex()
                else:
                    self.cycleinfo["firstnodeisolated"] +=1
                    #print("\n\nFIRSTNODESEGMENTS",self.firstnodesegments,self.lov,"\n\n")
                    self.undoLastVertex()
        else:
            #self.rebuildTemporaryPolygon(set(self.lov[:-1]))
            self.stuck = True
            


    def undoLastVertex(self):

        
        self.am.adjmatrix = self.oldadjmatrix
        # self.addnodesegments(self.firstnodesegments)

        # self.addnodesegments(self.qnodesegments)
        # self.addnodesegments(self.nvnodesegments)

        deadend = (self.lop[self.lov[-2]]["i"],self.lop[self.lov[-1]]["i"])
        self.currentdeadends.append(deadend)

        self.lov.pop()

    def removeIntersectSegments(self, p, q, listofsegments=None):

        if listofsegments:
            segments = listofsegments
        else:
            segments = self.am.getSegments()
        #print("SEGMENTS",segments)
        segmentstoberemoved = []
        for seg in segments:
            #print("seg",seg)
            r = self.loi[seg[0]]["v"]
            s = self.loi[seg[1]]["v"]

            if doIntersect(p,q,r,s):
                #print("p-q and r-s intersect",p,q,r,s)
                segmentstoberemoved.append(seg)

                # if seg in self.firstnodesegments:
                #     print("ATENCION",seg,self.firstnodesegments)
                #     self.firstnodesegments.remove(seg)
        self.am.adjmatrix.remove_edges_from(segmentstoberemoved)


    def restoreLastNodeSegments(self):
        self.addnodesegments(self.lastnodesegments)


    def getIsolatedParts(self):
        x = self.am.getConnectedComponents()
        return x

    def getIsolatedPartsAsListsOfPoints(self):
        parts = []
        x = self.am.getConnectedComponents()
        for i in x:
            one = []
            for e in i.edges:
                p = self.loi[e[0]]["v"]
                q = self.loi[e[1]]["v"]
                one.append((p,q))
            parts.append(one)

        return parts


    def numberofisolatedparts(self):
        return self.am.getNumberConnectedComponents()


def generate(vertexlist):


    num = 10
    results = []

    for i in range(num):
        ps = PolygonStruct(vertexlist)
        ps.setInitialVertex()

        while not ps.allPointsUsed():
            ps.cycle()
            if ps.stuck:
                break
            if ps.checkValidFinalPolygon():
                ps.lov.append(ps.initialvertex)
                results.append(ps.getJSON())
              
                break
    return results


app = Chalice(app_name='polygon')
app.debug = True


@app.route('/polygon/{vertexlist}')
def vertexlist(vertexlist):
    even = vertexlist.split(",")[0::2]
    odd = vertexlist.split(",")[1::2]

    vl = [(int(i),int(j)) for i,j in zip(even,odd)]
    
    return {'result': generate(vl)}


if __name__=="__main__":
    vertexlist = sys.argv[1]
    even = vertexlist.split(",")[0::2]
    odd = vertexlist.split(",")[1::2]

    vl = [(int(i),int(j)) for i,j in zip(even,odd)]
    print(vl,generate(vl))   