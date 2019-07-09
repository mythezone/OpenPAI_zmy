from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import json


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


class client(Thread):
    def __init__(self,msg,host='localhost',port=50001,msg_type='list'):
        Thread.__init__(self)
        print('init the client!')
        self.addr=(host,port)
        self.client=socket.socket()

        if msg_type=='string':
            self.msg=msg.encode()
        elif msg_type=='numpy':
            tmp=BytesIO()
            np.savetxt(tmp,msg)
            self.msg=tmp.getvalue()
        elif msg_type=='list':
            self.msg=str(msg).encode() #self.msg must be encoded.
        
    def run(self):
        self.client.connect(self.addr)
        self.client.send(self.msg)
        data=self.client.recv(8192)
        self.next_port=data.decode()
        print('recv:',self.next_port)
        self.client.close()

def msg_encode(msg,msg_type='list'):
    if msg_type=='list':
        return str(msg).encode()
    elif msg_type=='string':
        return msg.encode()
    elif msg_type=='numpy':
        tmp=BytesIO()
        np.savetxt(tmp,msg)
        msg=tmp.getvalue()
        return msg
    else:
        return 'not supported msg type(encode),plz check!'.encode()

def msg_decode(msg,msg_type='list'):
    if msg_type=='list':
        return eval(msg.decode())
    elif msg_type=='string':
        return msg.decode()
    elif msg_type=='numpy':
        return np.loadtxt(msg)
    else:
        return 'not supported msg type(decode),plz check!'

class messager:
    def __init__(self):
        self.client=socket.socket()

    def send_to(self,msg,host='localhost',port=50001):
        addr=(host,port)
        self.client.connect(addr)
        content=msg.msg_encode()
        self.client.send(content)
        self.recv=self.client.recv(8192).decode()
        statu,content=eval(self.recv)
        recv_msg=message(statu,content)
        recv_msg.show()
        self.client.close()
        return recv_msg


class server(Thread):
    def __init__(self,addr='localhost',port=50001,work=lambda x:x):
        Thread.__init__(self)
        print("init the server on port %d."%port)
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.addr=addr
        self.port=port
        try:
            self.s.bind((self.addr,self.port))
        except:
            print("bind error.")
        self.work=work

    def run(self):
        self.s.listen(5)
        while True:
            conn,addr=self.s.accept()
            print('Connect with:',addr)
            data=conn.recv(8192).decode()
            statu,content=eval(data) 
            msg=message(statu,content)         
            msg=self.work(msg)
            conn.send(msg)


def process(msg,route,algo,msgr):
    
    statu=msg.statu
    content=msg.content
    print("statu:",statu,'msg:',content)

    # process for different status
    if statu==101:
        route[content[0]]=content[1]
        print("One worker is ready.")

        if content[0]=='init':
            print("prepare to send message to the init service.")
            msg=message(666,'success in test')
            tmp_recv=msgr.send_to(msg,port=content[1])
            print(tmp_recv)

        return message(666,'success')
    else:
        while True:
            try:
                next_port=route[algo[statu]]
                break
            except:
                print("The port is not registed,pleas wait!")
                time.sleep(2)
        print('the next port is %d'%next_port)

    return message(666,next_port)

class master:
    def __init__(self,job_config='task_config.json'):
        with open(job_config,'r') as f:
            self.job_config=json.loads(f.read())
            self.algo_process=self.job_config['process']
        self.val_lock=Lock()
        self.route=dict()
        self.msgr=messager()
        self.port_work=server(port=50001,work=lambda x:process(x,route=self.route,algo=self.algo_process,msgr=self.msgr))
        

    def run(self):
        self.port_work.start()
        self.port_work.join()

class worker:
    def __init__(self,name,work):
        #select an avaliable port.
        self.port=np.random.randint(50005,59999)
        self.work=work
        self.name=name
        self.msgr=messager()
        while True:
            try:
                self.server=server(port=self.port,work=self.work)
                break
            except:
                self.port=np.random.randint(50005,59999)

        msg=message(101,[self.name,self.port])
        msg=self.msgr.send_to(msg)
        msg.show()
        
    def run(self):
        self.server.start()
        self.server.join()



if __name__=="__main__":
    mst=master()
    mst.run()
    