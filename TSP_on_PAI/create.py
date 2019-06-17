import numpy as np
import os,sys
import os_file as tos
#import matplotlib.pyplot as plt
import math
from pai_pyhdfs import *


work_path='/shared/TSP/'
hdfs_init_fold(work_path)


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

'''
private double distance(final double lat1, final double lon1, final double lat2, final double lon2) {
    final double theta = lon1 - lon2;
    double dist = Math.sin(deg2rad(lat1)) * Math.sin(deg2rad(lat2)) + Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) * Math.cos(deg2rad(theta));
    dist = Math.acos(dist);
    dist = rad2deg(dist);
    dist = dist * 60 * 1.1515;

    dist = dist * 1.609344;
    return (dist);
}
'''

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
    return matrix

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
    return np.random.permutation(num)

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

if __name__=="__main__":
    #tos.clean_work_path(work_path)
    cities=create_cities(100)
    hdfs_save(work_path,'cities.npy',cities)
    file_name='new_job.txt'
    with open(file_name,'w') as ff:
        ff.write('cities.npy')
    hdfs_set_file('./',work_path,file_name)
    