import numpy
import json
from functools import partial
import func_lib as fl
from base import message

class myclass:
    def __init__(self,a=10,b=15):
        self.a=a
        self.b=b

    def show(self):
        print(self.a,self.b)

    @staticmethod
    def show_num(k):
        if type(k) is int:
            print(k)
        else:
            print("this number is not a int.")

def myfunc(a,ob=None):
    print(a)
    print(ob.attr)

class worker:
    def __init__(self,func):
        self.func=partial(func,ob=self)
        self.attr='test'
    
    def run(self,num=4):
        self.func(num)

