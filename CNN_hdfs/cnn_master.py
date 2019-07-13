# coding=utf-8
import os,sys
import numpy as np
import time
#from pai_pyhdfs import *
from base import *
from multiprocessing import process
import multiprocessing
import json

class master_work(Process):
    def __init__(self,msg_list,jobconfig_path='task_config.json'):
        Process.__init__(self)
        with open(jobconfig_path,'r') as f:
            self.job_config=json.loads(f.read())
            self.algo=self.job_config['algo_statu']
            self.common=self.job_config['common_statu']
        self.route=dict()
        self.msg_list=msg_list

    def next_port(self,statu):
        name=self.algo[str(statu)]
        try:
            port=self.route[name]
            return port
        except:
            print("The port has not been registed!")

    

    def process(self,msg):
        statu,content=json.loads(msg)

        if statu==101:
            self.route[content[0]]=content[1]
            new_msg=message(669,'Port %d registed successfully!'%content[1])
            send_to(new_msg,port=content[1])
            return new_msg
        elif statu==102:
            route_msg=message(103,self.route)
            #not completed.
        else:
            port=self.next_port(statu)
            new_msg=message(666,port)
            send_to(new_msg,port=content)
            return new_msg
            

    def run(self):
        print("The handle of the message has been started!")
        while True:
            if self.msg_list.empty():
                time.sleep(2)
                continue
            else:
                msg=self.msg_list.get()
                print(msg)
                new_msg=self.process(msg)
                new_msg.show()

class master:
    def __init__(self,host='localhost',port=50001):
        self.msg_list=multiprocessing.Queue()
        self.server=server(self.msg_list,host=host,port=port)
        self.master_work=master_work(self.msg_list)

    def run(self):
        self.server.start()
        self.master_work.start()

if __name__=='__main__':
    m=master()
    m.run()
