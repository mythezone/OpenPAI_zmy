import create as tc
import numpy as np
import time
from pai_pyhdfs import *

work_path='/shared/TSP/'
nodes=10
num=100
population=10

while True:
    print("in the loop")
    f=wait_hdfs_file(work_path,'new_job.npy',delete=True)  #wait a start signal file.
    ff=wait_hdfs_file(work_path,'cities.npy',delete=False)  # wait problem discribe file.
    cities=np.load(ff,allow_pickle=True)
    print("calculating distance matrix...")
    dist=tc.distance_matrix(cities)
    print("saving file to the HDFS...")
    hdfs_save(work_path,'distance_matrix.npy',dist)

    #generate the total solutions and save it on the hdfs.
    generations=[]
    print("generate the solution of routes.")
    for i in range(nodes):
        routes=tc.init_solutions(population,num)
        generations.append(routes)

    hdfs_save(work_path,'generations.npy',generations)
    print("solution file setting over.waiting for results.")

    # wait for result and output it.Wati for next job.
    ff=wait_hdfs_file(work_path,'final_solution.npy',delete=True)
    msg,c=np.load(ff,allow_pickle=True)
    print("The final result of this TSP is : ",msg)
    print("The minimum cost of this problem is : ",c)
    print("waiting for the next job!")
