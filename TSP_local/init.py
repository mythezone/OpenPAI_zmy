import base_util as bu
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
        self.msgr=bu.messager()
        self.wkr=bu.worker('init',self.func)

    def func(self,msg):
        #cities=self.cities.tolist()
        print("server recved message:", msg.decode())
        msg=[0,1]
        while True:
            try:
                self.recv=self.msgr.send_to(msg)
                print("Recieved message: ",self.recv)
                # self.msgr.send_to(msg)
                # c=bu.client(msg,msg_type='list')
                # print("client has been initiated!")
                # c.start()
                # print('next_port:',c.next_port)
                # c.join()
                # #bu.send_msg(msg)
                # msg=[233,cities]
                # bu.send_msg(msg,port=c.next_port,msg_type='list')
                break
            except:
                print("There is something wrong with the program.")
                time.sleep(2)
        return str([911,'success']).encode()


    def send_content(self,content,port):
        content=content.tolist()
        msg=[233,content]
        c=bu.client(msg,port=port,msg_type='list')
        print("sending content.")
        c.start()
        c.join()

    def run(self):
        self.wkr.run()

if __name__=="__main__":
    wkr=init()
    wkr.run()