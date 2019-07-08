from threading import Thread
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64


class client():
    def __init__(self,msg,host='localhost',port=50001,msg_type='list'):
        print('init the client!')
        self.addr=(host,port)
        self.client=socket.socket()
        # self.msg=np.array(msg)
        # self.bytesio=BytesIO()
        # np.save(self.bytesio,self.msg)
        # self.msg=self.bytesio.getvalue()
        if msg_type=='string':
            self.msg=msg.encode()
        elif msg_type=='numpy':
            tmp=BytesIO()
            np.savetxt(tmp,msg)
            self.msg=tmp.getvalue()
        elif msg_type=='list':
            self.msg=str(msg).encode()
        
    def run(self):
        self.client.connect(self.addr)
        #msg="This is a message from the client!"
        #msg=np.random.uniform(size=(4,4))
        self.client.send(self.msg)
        data=self.client.recv(1024)
        print('recv:',data.decode())
        self.client.close()

if __name__=="__main__":
    msg=[101,['loop',50004]]

    #msg="['main',50004]".encode()
    c=client(msg,port=50001,msg_type='list')
    c.run()
    
    time.sleep(2)
    msg1=[1,[444,555,666]]
    c1=client(msg1)
    c1.run()

    # msg2='the message or worker.'.encode()
    # c2=client(msg=msg2,port=50012)
    # c2.run()