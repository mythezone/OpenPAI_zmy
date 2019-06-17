import create as tc
import os_file as to
import iteration as it
import numpy as np
import time,os,sys
from pai_pyhdfs import *
from pyspark.context import SparkContext
sc=SparkContext()

max_time=30*60
max_iter=10000
threshold=10.0
work_path='/shared/TSP/'
print("waiting for the matrix.")
f=wait_hdfs_file(work_path,'distance_matrix.npy',delete=False)
m=np.load(f)

def get_res(s1,s2):
    if tc.cost(s1,m)<tc.cost(s2,m):
        return s1
    else:
        return s2

print("start work.")

while True:
    f=wait_hdfs_file(work_path,'generations.npy',delete=False)
    generations=np.load(f)
    print("generation information getted. Now setting the gen_rdd.")
    gen_rdd=sc.parallelize(generations)
    print("rdd setted,now maping.")
    res=gen_rdd.map(it.iteration)
    print("mapping over,now reducing.")
    res2=res.reduce(get_res)
    print("The best solution is:",res2)
    c=tc.cost(res2,m)
    print("The lowest cost is :",c)
    hdfs_save(work_path,'final_solution.npy',[res2,c])
    #to.set_np_file(work_path,'final_solution.npy',[res2,c])


    # msg=to.wait_np_file_start(work_path,'solution',delete=True)
    # #print(msg)
    # solution,c_orig,file_name=msg
    # if file_name not in dic:
    #     dic[file_name]=[solution,c_orig,0]

    #     to.set_np_file(work_path,'cal_'+file_name[9:],msg)
    # else:
    #     dic[file_name][:2]=[solution,c_orig]
    #     dic[file_name][2]+=1
    #     if dic[file_name][2]==10:
    #         #print("Get one final solution.")
    #         final_res.append(dic[file_name][:2])
    #     else:
    #         to.set_np_file(work_path,'cal_'+file_name[9:],msg)
    
    # if len(final_res)==10:
    #     f=lambda x:x[1]
    #     msg=sorted(final_res,key=f)[0]
    #     solution,c=msg
    #     print("The best solution is :",solution)
    #     print("The lowest cost is : ",c)
    #     to.set_np_file(work_path,'final_solution.npy',msg)
    #     #os.remove(work_path+'distance_matrix.npy')
    #     dic=dict()
    #     final_res=[]
    #     print("Completed!!!Waiting for the next job!")
        
    #     time.sleep(10)
