from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import create as cr


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
        if self.port!=50001:
            msg='["loop",%d]'%port
            msg=msg.encode()
            send_port=client(msg)
            send_port.start()
            
        while True:
            conn,addr=self.s.accept()
            print('Connect with:',addr)
            data=conn.recv(4096)
            #arr=np.loadtxt(BytesIO(data))
            msg=self.work(data)
            print('recv:',data.decode())
            #msg='This is a message from the server!'
            conn.send(msg)
        #send_port.join()

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
        print('recv:',data.decode())
        self.client.close()

if __name__=="__main__":
    port=np.random.randint(51001,52000)
    s=server(port=port)
    s.start()
    
    # msg='["loop",%d]'%port
    # msg=msg.encode()
    # send_port=client(msg)
    # send_port.start()
    s.join()
    # send_port.join()