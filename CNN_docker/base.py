from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import json
import multiprocessing
from multiprocessing import Process
import func_lib as fl
from func_lib import message
import custom_func as cf


class server(Process):
    def __init__(self,ob=None,host='localhost',port=50001):
        Process.__init__(self)
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.host=host
        self.port=port
        self.ob=ob
        self.recv_list=ob.recv_list
        self.send_list=ob.send_list
        self.name=ob.name
        if type(port) is int:
            print("init the server on port %d."%port)
            try:
                self.s.bind((self.host,self.port))
            except:
                print("bind error.")
                exit()
        else:
            counter=0
            while True:
                try:
                    self.port=np.random.randint(50010,59999)
                    self.s.bind((self.host,self.port))
                    break
                except:
                    counter+=1
                    if counter>=10:
                        print("Tried 10 times but failed, check your code plz.")
                        break
                    continue

        #if this isnot the master server,then registe its port.
        if port!=50001:
            print("Now registing the port.")
            msg=message(50001,[101,[self.name,self.port]]).msg_encode()
            self.send_list.put(msg)
        
    def run(self):
        self.s.listen(10)
        while True:
            conn,_=self.s.accept()
            #print('Connect with:',addr)
            data=conn.recv(512000)
            print("server recvd data:",data)
            statu,content=json.loads(data.decode()) 
            if statu<400 or statu>=500:
                msg=message(statu,content)
                self.recv_list.put(msg.msg_encode())
                conn.send(message(466,'recved').msg_encode())
            else:
                print("Testing msg recvd:",statu,content)
            
class messager(Process):
    def __init__(self,ob=None,host='locahost',debug=False):
        super().__init__()
        print("Messager initiated.")
        self.s=socket.socket()
        self.ob=ob
        self.msg_list=self.ob.send_list
        self.route=self.ob.route
        self.host=host
        self.debug=debug

    def run(self):
        while True:
            if self.msg_list.empty():
                time.sleep(2)
                continue
            else:
                statu,content=json.loads(self.msg_list.get().decode())
                if statu<10000:
                    print("Wrong Statu in the sending list.")
                else:
                    print('msg',statu,content)
                    addr=(self.host,statu)
                    self.s.connect(addr)

                    new_msg=message(content[0],content[1]).msg_encode()
                    self.s.send(new_msg)
                    recv=self.s.recv(4096)
                    print(recv)
                    self.s.close()


class worker(Process):
    def __init__(self,recv_list,send_list,custom_func=dict(),ob=None):
        super().__init__()
        self.flib=fl.cstm_flib(custom_func,ob=ob)
        self.recv_list=recv_list
        self.send_list=send_list
        
    def run(self):
        while True:
            if self.recv_list.empty():
                time.sleep(2)
                #print("No msg in recvlist")
                continue
            else:
                print("There is a msg in recv_list")
                print("little change")
                msg=self.recv_list.get()
                new_msg=message.b2m(msg)
                new_msg.show()
                func=self.flib.get_by_statu(new_msg.statu)
                func.run(new_msg.content)
       
class micro_service:
    def __init__(self,recv_list,send_list,*args,func_dct=dict(),host='localhost',port=50001,name='service_name',**kargs):
        #super().__init__()
        self.recv_list=recv_list
        self.send_list=send_list
        self.args=args
        self.name=name
        self.kargs=kargs
        self.route=dict()
        self.dct=func_dct
        self.server=server(ob=self,host=host,port=port)
        self.messager=messager(self.send_list,host=host)
        self.worker=worker(self.recv_list,self.send_list,custom_func=self.dct,ob=self)

    def put_to_send_list(self,port,content):
        new_msg=message(port,content).msg_encode()
        self.send_list.put(new_msg)

    def run(self):
        self.server.start()
        self.messager.start()
        self.worker.start()
        

if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()

    ms=micro_service(recv_list,send_list,func_config='hello')
    ms.run()
