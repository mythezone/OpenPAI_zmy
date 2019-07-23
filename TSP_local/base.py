from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import json
import multiprocessing
from multiprocessing import Process
from log import generate_log_func

log_info = generate_log_func('file', 'network.txt')


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
        #return str(self.m).encode()
        msg=json.dumps(self.m).encode()
        return msg
    
    def msg_decode(self,msg):
        statu,content=json.loads(msg.decode())
        if statu==901:
            return content
        elif statu==902:
            return content
        else:
            log_info("check your msg type!")
        return content

    def show(self):
        log_info('statu: ',self.m[0],'; content: ',self.m[1])

class server(Process):
    def __init__(self,msg_list,host='localhost',port=50001):
        Process.__init__(self)
        log_info("init the server on port %d."%port)
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.host=host
        self.port=port
        self.msg_list=msg_list
        try:
            self.s.bind((self.host,self.port))
        except:
            log_info("bind error.")
            #exit()

    def run(self):
        self.s.listen(5)
        while True:
            conn,_=self.s.accept()
            #log_info('Connect with:',addr)
            data=conn.recv(512000)
            log_info("data:",data)
            statu,content=json.loads(data.decode()) 
            msg=message(statu,content)
            #msg.show()
            self.msg_list.put(msg.msg_encode())
            conn.send(message(669,'recved').msg_encode())
            

def send_to(msg,host='localhost',port=50001):
    client=socket.socket()
    addr=(host,port)
    client.connect(addr)
    content=msg.msg_encode()
    client.send(content)
    recv=client.recv(512000)
    statu,content=json.loads(recv.decode())
    recv_msg=message(statu,content)
    #recv_msg.show()
    client.close()
    return recv_msg
    

if __name__=="__main__":
    msgl=multiprocessing.Queue()

    s=server(msgl)
    s.start()
    log_info("Server started.")
