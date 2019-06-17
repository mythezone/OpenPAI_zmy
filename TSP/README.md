# TSP Problem on Spark

## Requires :

1. numpy
2. pyspark

## Example:

* cities number : 100
* generation : 1000
* population : 10
* crossover : first half of s1,the rest part of the solution are provided by s2 in order.
* mutation : swap random two cities.
* terminate condition : 1000 iteration or 180 seconds.

## Explaination:

1. The 'create.py' will create a random TSP with 100 cities and a new_job sign to weak up the 'main.py' program.
2. The 'main.py' program will read and delete the new_job sign and calculate the distance matrix of the cities(save in a .npy file). Then it will also randomly create a solutions file containing all the routes for evolution(also saved in a .npy file).
3. The 'tsp_loop.py' program will read the solutions and map them to the spark nodes for iteration. And reduce the result to get the best route of this TSP(save in file).
4. The 'main.py' will read the best route and print the information.Then waiting for the next job until exit manually.

## How to use this codes:

```bash
user $ sh run.sh
```
