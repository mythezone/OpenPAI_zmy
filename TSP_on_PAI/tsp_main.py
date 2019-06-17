import create as tc
import os_file as to
import numpy as np
import time
from pai_pyhdfs import *

work_path='/shared/TSP/'
nodes=10

time.sleep(3)

while True:
    f=wait_hdfs_file(work_path,'new_job.npy',delete=True)
    f2=wait_hdfs_file(work_path,'cities.npy',delete=False)
    #cities_file=to.wait_msg_file(work_path,'new_job.txt',delete=True)
    cities=np.load(f2)

    #cities=to.wait_np_file(work_path,cities_file,delete=False)
    #to.clean_work_path(work_path)
    dist=tc.distance_matrix(cities)
    hdfs_save(work_path,'distance_matrix.npy',dist)
    #to.set_np_file(work_path,'distance_matrix.npy',dist)
    num=len(cities)
    population=10
    
    generations=[]
    print("generate the solution of routes.")
    for i in range(nodes):
        routes=tc.init_solutions(population,num)
        generations.append(routes)
        # hash_num=np.random.randint(100000,999999)
        # file_name='solution_'+str(hash_num)+'.npy'
    hdfs_save(work_path,'generations.npy',generations)
    #to.set_np_file(work_path,'generations.npy',generations)
    print("solution file setting over.waiting for results.")
    # for i in range(population):
    #     hash_num=np.random.randint(100000,999999)
    #     file_name='solution_'+str(hash_num)+'.npy'
    #     to.set_np_file(work_path,file_name,np.array([solutions[i],9999999999999999,file_name]))
        
    ff=wait_hdfs_file(work_path,'final_solution.npy',delete=True)
    msg,c=np.load(ff)
    os.remove(ff)
    print("The final result of this TSP is : ",msg)
    print("The minimum cost of this problem is : ",c)
    print("waiting for the next job!")

    #to.clean_work_path(work_path)