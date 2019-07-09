from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import json
from queue import Queue


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

class message_list:
    def __init__(self):
        self.lst=Queue()
        self.lock=Lock()

    def add_msg(self,msg):
        self.lock.acquire()
        self.lst.put(msg)
        self.lock.release()

    def isEmpty(self):
        return self.lst.empty()

    def get_msg(self):
        if self.lst.empty()==False:
            self.lock.acquire()
            k=self.lst.get()
            self.lock.release()
            return k


def send_to(msg,host='localhost',port=50001):
    client=socket.socket()
    addr=(host,port)
    client.connect(addr)
    content=msg.msg_encode()
    client.send(content)
    recv=client.recv(8192).decode()
    statu,content=eval(recv)
    recv_msg=message(statu,content)
    recv_msg.show()
    client.close()
    return recv_msg
        
class server():
    def __init__(self,msg_list,host='localhost',port=50001):
        
        print("init the server on port %d."%port)
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.addr=addr
        self.port=port
        self.msg_list=msg_list
        try:
            self.s.bind((self.addr,self.port))
        except:
            print("bind error.")
            exit()

    def run(self):
        self.s.listen(5)
        while True:
            conn,addr=self.s.accept()
            print('Connect with:',addr)
            data=conn.recv(8192).decode()
            statu,content=eval(data) 
            msg=message(statu,content)
            
            conn.send(message(669,'recved'))
            self.msg_list.add_msg(msg)

def process(msg_list,route,algo):
    print("Message handle begin to work....")
    while True:
        if msg_list.isEmpty==False:
            statu,content=msg_list.get_msg()
            if statu==101:
                route[content[0]]=content[1]
            else:
                next_port=route[algo[statu]]
                msg=message(666,next_port)
                send_to(msg,content)

        else:
            print("No msg now")
            time.sleep(2)


class master:
    def __init__(self,job_config='task_config.json',work=process):
        with open(job_config,'r') as f:
            self.job_config=json.loads(f.read())
            self.algo_process=self.job_config['process']
        self.val_lock=Lock()
        self.route=dict()
        
        self.msg_list=message_list()
        self.message_handle=Thread(name='msg_handle',target=server, args=(self.msg_list,'localhost',50001))
        self.worker=Thread(name="worker",target=work,args=(self.msg_list,self.route,self.algo_process))
        

    def run(self):
        self.message_handle.start()
        self.worker.start()
        

class worker:
    def __init__(self,name,work):
        #select an avaliable port.
        self.port=np.random.randint(50005,59999)
        self.work=work
        self.name=name
        self.msg_list=message_list()
        
        while True:
            try:
                self.message_handle=Thread(name='msg_handle',target=server,agrs=(mself.msg_list,'localhost',self.port))
                #self.worker=Thread(name="worker",target=work(msg_list=self.msg_list))
                break
            except:
                self.port=np.random.randint(50005,59999)

        msg=message(101,[self.name,self.port])
        send_to(msg)
        time.sleep(1)
        send_to(msg)
        #self.msgr.recv.show()
        
    def run(self):
        self.message_handle.start()
        #self.worker.start()



if __name__=="__main__":
    mst=master()
    mst.run()
    