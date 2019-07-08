from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import json


'''
master server for port registry is : 50001
'''

def port_check(port):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.connect(('localhost',int(port)))
        s.shutdown(2)
        return True
    except:
        return False

class client():
    def __init__(self,msg,host='localhost',port=50001,msg_type='list'):
        
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
        data=self.client.recv(1024)
        print('recv:',data.decode())
        self.client.close()

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

def save_route(msg,route,val_lock):
    '''
    format of msg: ['name',port]
    '''
    msg=eval(msg.decode())
    val_lock.acquire()
    route[msg[0]]=msg[1]
    val_lock.release()
    #try to send message to the recieved port.
    m='recieved the port of %s : %d'%(msg[0],msg[1])
    try:
        c=client(msg=m.encode(),port=msg[1])
        c.start()
        c.join()
    except:
        print("The port of %s is inavailable!"%msg[0])

    return 'route updated!'.encode()

def process(msg,route,algo):
    statu,msg=eval(msg.decode())
    statu=str(statu)
    
    print("statu:",statu,'msg:',msg)

    # process for different status
    if statu=='101':
        route[msg[0]]=msg[1]
        print("One worker is ready.")
    else:
        while True:
            try:
                next_port=route[algo[statu]]
                break
            except:
                print("The port is not registed,pleas wait!")
                time.sleep(2)
        print('the next port is %d'%next_port)
        tmp_client=client(msg,port=next_port)
        
        #Try to send message to the distinct port.
        while True:
            try:
                tmp_client.run()
                break
            except:
                pass
    return 'recieved your work!'.encode()

class master:
    def __init__(self,job_config='task_config.json'):
        with open(job_config,'r') as f:
            self.job_config=json.loads(f.read())
            self.algo_process=self.job_config['process']
        self.val_lock=Lock()
        self.route=dict()
        #self.port_register=server(work=lambda x:save_route(x,route=self.route,val_lock=self.val_lock))
        self.port_work=server(port=50001,work=lambda x:process(x,route=self.route,algo=self.algo_process))
        

    def run(self):
        self.port_work.start()
        self.port_work.join()

class worker:
    def __init__(self,name,work):
        #select an avaliable port.
        self.port=np.random.randint(50005,59999)
        self.work=work
        self.name=name
        while True:
            try:
                self.server=server(port=self.port,work=self.work)
                break
            except:
                self.port=np.random.randint(50005,59999)

        msg=[101,[self.name,self.port]]
        self.port_reg=client(msg)
        self.port_reg.run()

    def run(self):
        self.server.start()
        self.server.join()



if __name__=="__main__":
    mst=master()
    mst.run()
    