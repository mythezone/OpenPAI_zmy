import create as tc
import os_file as to
import numpy as np
import time,os,sys

threshold=1.0
work_path='./work/'
# m=to.wait_np_file(work_path,'distance_matrix.npy',delete=False)
dic=dict()
final_res=[]

while True:
    
    msg=to.wait_np_file_start(work_path,'solution',delete=True)
    #print(msg)
    solution,c_orig,file_name=msg
    if file_name not in dic:
        dic[file_name]=[solution,c_orig,0]

        to.set_np_file(work_path,'cal_'+file_name[9:],msg)
    else:
        dic[file_name][:2]=[solution,c_orig]
        dic[file_name][2]+=1
        if dic[file_name][2]==10:
            #print("Get one final solution.")
            final_res.append(dic[file_name][:2])
        else:
            to.set_np_file(work_path,'cal_'+file_name[9:],msg)
    
    if len(final_res)==10:
        f=lambda x:x[1]
        msg=sorted(final_res,key=f)[0]
        solution,c=msg
        print("The best solution is :",solution)
        print("The lowest cost is : ",c)
        to.set_np_file(work_path,'final_solution.npy',msg)
        #os.remove(work_path+'distance_matrix.npy')
        dic=dict()
        final_res=[]
        print("Completed!!!Waiting for the next job!")
        
        time.sleep(10)
