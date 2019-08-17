import numpy as np
import json
from functools import partial
import caffe
import time
import sys,os
sys.path.insert(0, './python/')
import ncs
from base import *
from easydict import EasyDict as edict
import pdb
from base import *
import multiprocessing

route=dict({
    'master':50001,
    'main':50002,
    'loop1':50003,
    'loop2':50004,
    'evaluator':50005,
})

algo={
    2:'loop1',
    3:'loop2',
    31:['loop2','evaluator'],
    32:['loop2','evaluator'],
    33:['loop2','evaluator'],
    34:'loop2',
    35:'loop1',
    41:'evaluator',
    51:'loop2',
    101:'register',
}

class worker(Process):
    def __init__(self,recv_list,send_list,route=route,algo_route=algo):
        Process.__init__(self)
        self.recv_list=recv_list
        self.send_list=send_list
        self.route=route
        self.algo_route=algo_route

    def run(self):
        print("Master is running:")
        while True:

            if self.recv_list.empty():
                time.sleep(2)
                continue
            else:
                msg=self.recv_list.get()
                print("Get a message:",msg.decode())
                new_msg=message.b2m(msg)
                statu,_content=new_msg.statu,new_msg.content
                
                if statu==101:
                    self.route[_content[0]]=_content[1]
                    print("registed successfully.")
                    print("now the route is : ",self.route)
                    continue
                elif statu==102:
                    _statu,file_name,file_path=_content
                    if _statu in self.algo_route:
                        next_name=self.algo_route[_statu]
                        if type(next_name)==list:
                            for i_name in next_name:
                                if i_name not in self.route:
                                    print("wrong route:",i_name)
                                else:
                                    new_msg=message(statu,[self.route[i_name],file_name,file_path]).msg_encode()
                                    self.send_list.put(new_msg)
                        else:
                            next_port=self.route[next_name]
                            new_msg=message(statu,[next_port,file_name,file_path]).msg_encode()
                            self.send_list.put(new_msg)
                    else:
                        print("get a wrong statu:",_statu)
                    
                    print("file message has been transimited.")

                elif statu<100:
                    if statu not in self.algo_route:
                        print("wrong statu:",statu)
                        continue
                    next_name=self.algo_route[statu]

                    if type(next_name)==list:
                        for i_name in next_name:
                            if i_name not in self.route:
                                print("wrong route:",i_name)
                            else:
                                new_msg=message(self.route[i_name],[statu,_content]).msg_encode()
                                self.send_list.put(new_msg)
                        print("all message have been transited...")
                    else:
                        next_port=self.route[next_name]
                        print('next_name',next_name,'next_port',next_port)
                        new_msg=message(next_port,[statu,_content]).msg_encode()
                        self.send_list.put(new_msg)
                        print("message has been transited...")
                        continue

                    


if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()
    ser=server(recv_list,send_list)
    mgr=messager(recv_list,send_list)
    wkr=worker(recv_list,send_list)

    mgr.start()
    ser.start()
    wkr.start()
    print("main process over")
