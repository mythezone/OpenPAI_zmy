import create as tc
import numpy as np
import time
from pai_pyhdfs import *

work_path='/shared/TSP/'
nodes=10
num=100
population=10

print("Detection started!")
while True:
    print("In the loop.")
    generations=[]
    print("generate the solution of routes.")
    for i in range(nodes):
        routes=tc.init_solutions(population,num)
        generations.append(routes)

    hdfs_save(work_path,'generations.npy',generations)
    print("solution file setting over.waiting for results.")

    ff=wait_hdfs_file(work_path,'final_solution.npy',delete=True)
    msg,c=np.load(ff)
    print("The final result of this TSP is : ",msg)
    print("The minimum cost of this problem is : ",c)
    print("waiting for the next job!")
