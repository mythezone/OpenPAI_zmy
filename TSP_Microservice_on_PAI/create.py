import numpy as np
import os,sys
import math
import time




work_path='./work/'

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


def next_generation(solutions,matrix):
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
    sorted_solutions=sorted(solutions,key=lambda x:cost(x,matrix))[:length]
    return np.array(sorted_solutions)

def iteration(solutions,matrix,max_iteration=100,max_time=180):
    start=time.time()
    time_escaped=0
    iter=0
    while iter<max_iteration and time_escaped<max_time:
        solutions=next_generation(solutions,matrix)
        iter+=1
        time_escaped=time.time()-start
        #print("This is the %d-th iteration."%iter)
        #print("solutions[0]",solutions[0])
    #print("This iteration is over.")
    return solutions[0]


def create_city(low=0,up=90):
    x=np.random.uniform(low,up,2)
    return x


def create_cities(num=100):
    cities=np.random.uniform(0,90,(num,2))
    return cities

def save_data(num=100):
    cities=create_cities(num)
    files=os.listdir(work_path)
    if 'work' not in files:
        os.mkdir(work_path)
    np.save(work_path+'cities.npy',cities)

def load_data(filepath):
    cities=np.load(filepath)
    return cities

def dist(city1,city2):
    theta=city1[0]-city2[0]
    dist=math.sin(math.radians(city1[1]))*math.sin(math.radians(city2[1]))+math.cos(math.radians(city1[1]))*math.cos(math.radians(city2[1]))*math.cos(theta)
    dist=math.acos(dist)
    dist=math.degrees(dist)
    dist=dist*60*1.1515
    dist=dist*1.609344
    return dist

def distance_matrix(cities):
    num=len(cities)
    matrix=np.zeros((num,num))
    for i in range(num):
        for j in range(i+1,num):
            matrix[i][j]=dist(cities[i],cities[j])
            matrix[j][i]=matrix[i][j]
    return matrix.tolist()

def cost(solution,matrix):
    #tmp=np.copy(solution)
    tmp=np.append(solution,solution[0])
    #print("tmp",tmp)
    n=len(solution)
    cost=0
    for i in range(n):
        cost+=matrix[tmp[i]][tmp[i+1]]
    return cost

def random_solution(num=100):
    return np.random.permutation(num).tolist()

def init_solutions(num=10,cities=100):
    solutions=[]
    for i in range(num):
        solutions.append(random_solution(cities))
    return solutions

def mutation_1(solution):
    n=len(solution)
    start=np.random.randint(0,n-2)
    end=np.random.randint(start+1,n)
    k=solution[start:end]
    solution[start:end]=k[::-1]
    return solution

def mutation_2(solution):
    n=len(solution)
    start=np.random.randint(0,n-2)
    end=np.random.randint(start+1,n)
    k=solution[start]
    solution[start:end-1]=solution[start+1:end]
    solution[end-1]=k
    return solution


#-----used for create a new TSP------------#
if __name__=="__main__":
    #tos.clean_work_path(work_path)
    cities=create_cities(100)
    np.save(work_path+'cities.npy',cities)

    # file_name='new_job.txt'
    # with open(file_name,'w') as ff:
    #     ff.write('cities.npy')
    # hdfs_set_file('./',work_path,file_name)
    