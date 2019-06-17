import create as tc
import os_file as to
import numpy as np
import time
from pai_pyhdfs import *

work_path='/shared/TSP/'
f=wait_hdfs_file(work_path,'distance_matrix.npy',delete=False)
m=np.load(f)
#m=to.wait_np_file(work_path,'distance_matrix.npy')



def cross(s1,s2):
    length=len(s1)
    res=[s1[i] for i in range(length//2)]
    #res=s1[:length//2]
    for i in range(length//2,length):
        if s2[i] not in res:
            res.append(s2[i])
    for i in range(length//2):
        if s2[i] not in res:
            res.append(s2[i])
    return np.array(res)

def mutation(s):
    lenght=len(s)
    a,b=np.random.permutation(lenght)[:2]
    s[a],s[b]=s[b],s[a]
    return s

def cross_and_mutation(s1,s2):
    child=cross(s1,s2)
    return mutation(child)


def next_generation(solutions,matrix=m):
    length=len(solutions)
    tmp=[]
    for i in range(length):
        for j in range(length):
            if i!=j:
                tmp.append(cross_and_mutation(solutions[i],solutions[j]))
    tmp=np.array(tmp)
    #print("tmp.shape",tmp.shape)
    #print(solutions.shape)
    solutions=np.vstack((solutions,tmp))
    sorted_solutions=sorted(solutions,key=lambda x:tc.cost(x,matrix))[:length]
    return np.array(sorted_solutions)

def iteration(solutions,max_iteration=100,max_time=180):
    start=time.time()
    time_escaped=0
    iter=0
    while iter<max_iteration and time_escaped<max_time:
        solutions=next_generation(solutions)
        iter+=1
        time_escaped=time.time()-start
        #print("This is the %d-th iteration."%iter)
        #print("solutions[0]",solutions[0])
    #print("This iteration is over.")
    return solutions[0]





