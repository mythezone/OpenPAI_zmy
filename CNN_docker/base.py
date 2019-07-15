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


# class message:
#     '''
#     "901":"string",
#     "902":"list",
#     "903":"numpy",
#     "904":"file"
#     '''
#     def __init__(self,statu,content):
#         self.statu=statu
#         self.content=content
#         self.m=[statu,content]

#     def msg_encode(self):
#         #return str(self.m).encode()
#         msg=json.dumps(self.m).encode()
#         return msg

#     #@staticmethod
#     def msg_decode(self,msg):
#         statu,content=json.loads(msg.decode())
#         if statu==901:
#             return content
#         elif statu==902:
#             return content
#         else:
#             print("check your msg type!")
#         return content

#     @staticmethod
#     def b2m(msg):
#         """
#         a static method of the class message,used to change the binary message recvd from the socket into a message class entity.
#         """
#         tmp=msg.decode()
#         statu,content=json.loads(tmp)
#         return message(statu,content)

#     def show(self):
#         print('statu: ',self.m[0],'; content: ',self.m[1])

class server(Process):
    def __init__(self,msg_list,name='noname',host='localhost',port=50001):
        Process.__init__(self)
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.host=host
        self.port=port
        self.msg_list=msg_list
        self.name=name
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
            msg=message(101,[self.name,self.port])
            self.msg_list.put(msg.msg_encode())
        
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
                self.msg_list.put(msg.msg_encode())
                conn.send(message(466,'recved').msg_encode())
            else:
                print("Testing msg recvd:",statu,content)
            
class messager(Process):
    def __init__(self,msg_list,host='locahost',debug=False):
        super().__init__()
        print("Messager initiated.")
        self.s=socket.socket()
        self.msg_list=msg_list
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
                    addr=(self.host,statu)
                    self.s.connect(addr)
                    self.s.send(content)
                    recv=self.s.recv(4096)

                    #show debug information.
                    if self.debug==True:
                        tmp1,tmp2=json.loads(recv.decode())
                        print("statu:",tmp1,'\ncontent:',tmp2)
                    self.s.close()

# def send_to(msg,host='localhost',port=50001):
#     client=socket.socket()
#     addr=(host,port)
#     client.connect(addr)
#     content=msg.msg_encode()
#     client.send(content)
#     recv=client.recv(512000)
#     statu,content=json.loads(recv.decode())
#     recv_msg=message(statu,content)
#     #recv_msg.show()
#     client.close()
#     return recv_msg

class handler:
    def __init__(self,config='handler_config.json'):
        with open(config,'r') as ff:
            self.statu_to_func=json.loads(ff.read())['statu_to_func']
        
    def get_func(self,statu):
        func_name=self.statu_to_func[str(statu)]
        return eval("fl.%s"%func_name)


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
                continue
            else:
                msg=self.recv_list.get()
                new_msg=message.b2m(msg)
                func=self.flib.get_by_statu(new_msg.statu)
                func.run(new_msg.content)

    def send_or_remain(self,msg):
        statu=msg.statu
        if statu>10000:
            self.send_list.put(msg)
        else:
            self.recv_list.put(msg)
        
class micro_service(Process):
    def __init__(self,recv_list,send_list,func_config='',*args,port=50001,host='localhost',name='service_name',**kargs):
        super().__init__()
        self.recv_list=recv_list
        self.send_list=send_list
        self.args=args
        self.name=name
        self.kargs=kargs
        self.route=dict()
        self.dct=cf.profile().d
        self.server=server(self.recv_list,name=name,host=host,port=port)
        self.messager=messager(self.send_list,host=host)
        self.worker=worker(self.recv_list,self.send_list,custom_func=self.dct,ob=self)

    def put_to_send_list(self,port,msg):
        new_msg=message(port,msg).msg_encode()
        self.send_list.put(new_msg)

    def put_to_recv_list(self,msg):
        new_msg=msg.msg_encode()
        self.recv_list.put(new_msg)

    def run(self):
        self.server.run()
        self.messager.run()
        self.worker.run()
        pass

if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()

    ms=micro_service(recv_list,send_list,func_config='hello')
    ms.start()
