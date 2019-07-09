from base_util import *
import numpy as np
import os,sys,time,json
import create as cr
from io import BytesIO
from threading import Thread
#-----problem initiate---------#


class init:
    def __init__(self,population=10,notes=10,cities=100):
        self.population=population
        self.notes=notes
        self.cities=cr.create_cities(cities)
        self.wkr=worker('init',self.func)

    def func(self,msg):
        #cities=self.cities.tolist()
        print("Init program has recvd a msg as following:")
        msg.show()
        msg=message(666,'test success.')
        while True:
            try:
                self.msgr.send_to(msg)
                #self.msgr.recv.show()
                break
            except:
                print("There is something wrong with the program.")
                time.sleep(2)
        return message(911,'success')
        
    def run(self):
        self.wkr.run()

if __name__=="__main__":
    wkr=init()
    wkr.run()