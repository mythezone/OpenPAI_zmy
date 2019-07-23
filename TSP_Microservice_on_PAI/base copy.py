from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import json
import multiprocessing
from multiprocessing import Process


class message:
    '''
    "901":"string",
    "902":"list",
    "903":"numpy",
    "904":"file"
    '''
    def __init__(self,statu,content):
        self.statu=statu
        self.content=content
        self.m=[statu,content]

    def msg_encode(self):
        return str(self.m).encode()
    
    def msg_decode(self,msg):
        statu,content=eval(msg)
        if statu==901:
            return content
        elif statu==902:
            return content
        else:
            print("check your msg type!")
        return content

    def show(self):
        print('statu: ',self.m[0],'; content: ',self.m[1])

class server(Process):
    def __init__(self,msg_list,host='localhost',port=50001):
        Process.__init__(self)
        print("init the server on port %d."%port)
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.host=host
        self.port=port
        self.msg_list=msg_list
        try:
            self.s.bind((self.host,self.port))
        except:
            print("bind error.")
            exit()

    def run(self):
        self.s.listen(5)
        while True:
            conn,addr=self.s.accept()
            #print('Connect with:',addr)
            data=conn.recv(51200).decode()
            statu,content=eval(data) 
            msg=message(statu,content)
            #msg.show()
            self.msg_list.put(msg.msg_encode())
            conn.send(message(669,'recved').msg_encode())

class message_handler(Process):
    def __init__(self,handler,route,msg_list):
        Process.__init__(self)
        self.handler=handler
        self.route=route
        self.msg_list=msg_list

    def route_update(self,msg):
        self.route[msg.statu]=msg.content

    def route_get(self,msg):
        if msg.statu in self.route:
            return self.route[msg.statu]
        else:
            return 0

    def process(self,msg):
        try:
            new_msg=self.handler(msg)
            return new_msg
        except:
            return message(404,'error')

    def run(self):
        while True:
            if self.msg_list.empty():
                time.sleep(2)
            else:
                msg=self.msg_list.get()



def send_to(msg,host='localhost',port=50001):
    client=socket.socket()
    addr=(host,port)
    client.connect(addr)
    content=msg.msg_encode()
    client.send(content)
    recv=client.recv(51200).decode()
    statu,content=eval(recv)
    recv_msg=message(statu,content)
    #recv_msg.show()
    client.close()
    return recv_msg
    



if __name__=="__main__":
    msgl=multiprocessing.Queue()

    s=server(msgl)
    s.start()
    print("Server started.")
