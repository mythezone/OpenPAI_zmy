import base_util as bu
import numpy as np
import os,sys,time,json
import create as cr
from io import BytesIO

#-----problem initiate---------#


class init:
    def __init__(self,population=10,notes=10,cities=100):
        self.population=population
        self.notes=notes
        self.cities=cr.create_cities(cities)

        self.wkr=bu.worker('init',self.func)

    def func(self,msg):
        msg=eval(msg.decode())
        tmp=BytesIO()
        np.savetxt(tmp,self.cities)


        pass

    def run(self):
        self.wkr.run()

if __name__=="__main__":
    wkr=bu.worker('loop',lambda x:x)
    wkr.run()