import create as tc
import os_file as to
import numpy as np

work_path='./TSP/work/'

while True:
    cities_file=to.wait_msg_file(work_path,'new_job.txt',delete=True)
    cities=to.wait_np_file(work_path,cities_file,delete=True)
    to.clean_work_path(work_path)
    dist=tc.distance_matrix(cities)
    to.set_np_file(work_path,'distance_matrix.npy',dist)
    num=len(cities)
    population=10
    solutions=tc.init_solutions(population,num)

    for i in range(population):
        hash_num=np.random.randint(100000,999999)
        file_name='solution_'+str(hash_num)+'.npy'
        to.set_np_file(work_path,file_name,np.array([solutions[i],9999999999999999,file_name]))
        

    msg,c,name=to.wait_msg_file(work_path,'final_solution.npy')
    
    print("The final result of this TSP is : ",msg)
    print("The minimum cost of this problem is : ",c)

    to.clean_work_path(work_path)