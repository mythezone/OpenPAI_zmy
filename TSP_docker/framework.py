from threading import Thread
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64


class server(Thread):
    def __init__(self,addr='localhost',port=50001,work=lambda x:x):
        Thread.__init__(self)
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
            self.work(data)
            print('recv:',data.decode())
            msg='This is a message from the server!'
            conn.send(msg.encode())


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

# def send_msg(msg,host='localhost',port=50001):
#     c=client(msg,host,port)
#     c.start()
#     c.join()
#     print("This threading is over.")


class framework:
    def __init__(self,func):
        self.server=server()
        # msg=np.random.uniform(size=(4,4))
        # bytesio=BytesIO()
        # np.savetxt(bytesio,msg)
        # msg=bytesio.getvalue()
        msg="text msg!".encode()
        self.client=client(msg)
    
    def run(self):
        self.server.start()
        time.sleep(2)
        self.client.start()
        self.server.join()
        self.client.join()

class master:
    def __init__(self):
        self.server=server('localhost',port=50002)
        self.route=dict()
        


if __name__=="__main__":
    f=framework(lambda x:x+1)
    f.run()
    print("main process is over!")
    #send_msg('hello,world!'.encode())
        
