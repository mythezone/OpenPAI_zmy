from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64


class server():
    def __init__(self,addr='localhost',port=50001,work=lambda x:x):
        print("init the server.")
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        # port=np.random.randint(50000,59999)
        port=50001
        try:
            self.s.bind((addr,port))
        except:
            print("bind error.")
        self.work=work


    def run(self):
        self.s.listen(5)
        while True:
            conn,addr=self.s.accept()
            print('Connect with:',addr)
            data=conn.recv(4096)
            #arr=np.loadtxt(BytesIO(data))
            msg=self.work(data)
            print('recv:',data.decode())
            #msg='This is a message from the server!'
            conn.send(msg)


#val_lock=Lock()

def save_route(msg,route):
    msg=eval(msg.decode())
    #val_lock.acquire()
    route[msg[0]]=msg[1]
    #val_lock.release()
    print(msg)
    print(route)
    return 'route updated!'.encode()

if __name__=="__main__":
    route=dict()
    s=server(work=lambda x:save_route(x,route=route))
    s.run()