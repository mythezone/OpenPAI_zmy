# TSP Problem on Spark

## Requires :

1. numpy
2. pyspark

## image :

"registry.cn-hangzhou.aliyuncs.com/lgy_sustech/spark:v1"

## jobConfig :

```json
{
    "jobName": "demo2-tsp",
    "image": "registry.cn-hangzhou.aliyuncs.com/lgy_sustech/spark:v1",
    "virtualCluster": "default",
    "taskRoles": [
      {
        "name": "create_job",
        "taskNumber": 1,
        "cpuNumber": 2,
        "memoryMB": 8192,
        "gpuNumber": 0,
        "command": "git clone https://github.com/mythezone/OpenPAI_zmy.git   && cd OpenPAI_zmy/TSP_on_PAI &&  python3 create.py "
      },
      {
        "name": "tsp_main",
        "taskNumber": 1,
        "cpuNumber": 2,
        "memoryMB": 8192,
        "gpuNumber": 0,
        "command": "git clone https://github.com/mythezone/OpenPAI_zmy.git   && cd OpenPAI_zmy/TSP_on_PAI  &&  python3 tsp_main.py "
      },
      {
        "name": "convert",
        "taskNumber": 1,
        "cpuNumber": 1,
        "memoryMB": 2048,
        "gpuNumber": 0,
        "command": "git clone https://github.com/mythezone/OpenPAI_zmy.git   && cd OpenPAI_zmy/TSP_on_PAI  &&  spark-submit --master local[4] tsp_loop.py",
        "shmMB": 64,
        "minFailedTaskCount": 1
      }
    ]
  }
```

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

## Details of iteration:

1. The individual of the map function is the routes (size of population.)
2. Every two different route in the individual will crossover with the rest routes.(So we get n*(n-1) children).
3. All the children will mutate by swapping random two cities.
4. All the children will be added into the individual and sorted by the cost.(n*n routes in order.)
5. Select the first population size routes as the next generation.

