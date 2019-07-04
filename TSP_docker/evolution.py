import create as tc
import os_file as to
import numpy as np
import time

work_path='./work/'
m=to.wait_np_file(work_path,'distance_matrix.npy')

while True:
    s_orig,c_orig,name=to.wait_np_file_start(work_path,'cal',delete=True)
    s=tc.mutation_1(s_orig)
    c=tc.cost(s,m)
    if c<c_orig:
        s_orig=s
        c_orig=c
    s=tc.mutation_2(s_orig)
    c=tc.cost(s,m)
    if c<c_orig:
        s_orig=s
        c_orig=c
    res=np.array([s_orig,c_orig,name])
    to.set_np_file(work_path,name,res)
    