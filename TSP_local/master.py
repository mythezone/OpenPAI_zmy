from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import create as cr
import json


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

class client(Thread):
    def __init__(self,msg,host='localhost',port=50001):
        Thread.__init__(self)
        print('init the client!')
        self.addr=(host,port)
        self.client=socket.socket()
        # self.msg=np.array(msg)
        # self.bytesio=BytesIO()
        # np.save(self.bytesio,self.msg)
        # self.msg=self.bytesio.getvalue()
        self.msg=msg
        
    def run(self):
        self.client.connect(self.addr)
        #msg="This is a message from the client!"
        #msg=np.random.uniform(size=(4,4))
        self.client.send(self.msg)
        data=self.client.recv(1024)
        #print('recv:',data.decode())
        self.client.close()



val_lock=Lock()

def save_route(msg,route):
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

def process(msg,route):
    statu,msg=eval(msg.decode())
    #msg=eval(msg.decode())
    print("statu:",statu)
    print('msg:',msg)
    return 'recieved your work!'.encode()


if __name__=="__main__":
    # #--------init problem----------#
    # cities=np.load('./work/cities.npy')
    # #print(cities[:10])
    # dist_matrix=cr.distance_matrix(cities)
    # #print(dist_matrix[:10])
    # population=10
    # num=len(cities)

    # generations=[]
    # for i in range(population):
    #     routes=cr.init_solutions(population,num)
    #     generations.append(routes)
    job_proc=[]
    algo_proc=[]
    with open("task_config.json",'r') as f:
        job_proc=json.loads(f.read())
        algo_proc=job_proc['process']
    print(algo_proc)
        

    route=dict()
    s=server(work=lambda x:save_route(x,route=route))
    s2=server(port=50012,work=lambda x:process(x,route=route))
    s2.start()
    s.start()
    s.join()
    s2.join()