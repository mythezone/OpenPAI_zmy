import numpy as np
import json
from functools import partial

d=dict()

func1=lambda x,ob=None:x+1

func2=lambda x,ob=None:x+2

def func3(x,ob=None):
    print(ob.route)
    return x**4


class profile:
    def __init__(self):
        self.d=dict()
        self.d[410]=func1
        self.d[411]=func2
        self.d[412]=func3