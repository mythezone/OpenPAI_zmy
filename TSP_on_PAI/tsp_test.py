import sys
from random import random
from operator import add
# from pai_pyhdfs import *
from pyspark.sql import SparkSession


if __name__ == "__main__":
    """
        Usage: pi [partitions]
    """
    print("start init spark.")
    spark = SparkSession\
        .builder\
        .appName("PythonPi")\
        .getOrCreate()

    #import create
    partitions = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    n = 100000 * partitions
    # #import numpy as np
    # c=np.array([1,2,3])
    # print(c)
    def f(_):
        x = random() * 2 - 1
        y = random() * 2 - 1
        return 1 if x ** 2 + y ** 2 <= 1 else 0

    count = spark.sparkContext.parallelize(range(1, n + 1), partitions).map(f).reduce(add)
    print("Pi is roughly %f" % (4.0 * count / n))

    spark.stop()
    print("spark stoped.")
