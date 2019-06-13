import TSP.create as tc
import TSP.os_file as to
import numpy as np

cities=tc.load_data("./TSP/work/cities.npy")
dist=tc.distance_matrix(cities)
to.set_np_file('./TSP/work/','distance_matrix.npy',dist)
num=len(cities)
population=10
solutions=tc.init_solutions(population,num)

solution=tc.random_solution(len(cities))
c=tc.cost(solution,dist)
print(c)