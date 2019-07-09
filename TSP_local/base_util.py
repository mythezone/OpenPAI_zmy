from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import json


class msg:
    '''
    "901":"string",
    "902":"list",
    "903":"numpy",
    "904":"file"
    '''
    def __init__(self,statu,content):
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

    def send_to(self,msg,host='localhost',port=50001,msg_type='list'):
        addr=(host,port)
        self.client.connect(addr)
        msg=msg_encode(msg)
        self.client.send(msg)
        self.recv=self.client.recv(8192)
        #print('recv : ',self.recv.decode())
        self.client.close()
        return self.recv


class server(Thread):
    def __init__(self,addr='localhost',port=50001,work=lambda x:x):
        Thread.__init__(self)
        print("init the server on port %d."%port)
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        # port=np.random.randint(50000,59999)
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
            data=conn.recv(8192)
            #arr=np.loadtxt(BytesIO(data))
            msg=self.work(data)
            #print('recv:',data.decode())
            #msg='This is a message from the server!'
            conn.send(msg)


def process(msg,route,algo,msgr):
    statu,msg=eval(msg.decode())
    statu=str(statu)
    
    print("statu:",statu,'msg:',msg)

    # process for different status
    if statu=='101':
        route[msg[0]]=msg[1]
        print("One worker is ready.")

        if msg[0]=='init':
            strt='begin'
            msgr.send_to(strt,port=msg[1],msg_type='string')

        return "Port registed successfully.".encode()
    else:
        while True:
            try:
                next_port=route[algo[statu]]
                break
            except:
                print("The port is not registed,pleas wait!")
                time.sleep(2)
        print('the next port is %d'%next_port)

    return str(next_port).encode()

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
        #self.msgr=messager()
        while True:
            try:
                self.server=server(port=self.port,work=self.work)
                break
            except:
                self.port=np.random.randint(50005,59999)

        msg=[101,[self.name,self.port]]
        self.port_reg=client(msg)
        

    def run(self):
        self.port_reg.start()
        self.server.start()
        self.port_reg.join()
        self.server.join()



if __name__=="__main__":
    mst=master()
    mst.run()
    