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
        #return str(self.m).encode()
        msg=json.dumps(self.m).encode()
        return msg

    #@staticmethod
    def msg_decode(self,msg):
        statu,content=json.loads(msg.decode())
        if statu==901:
            return content
        elif statu==902:
            return content
        else:
            print("check your msg type!")
        return content

    @staticmethod
    def b2m(msg):
        """
        a static method of the class message,used to change the binary message recvd from the socket into a message class entity.
        """
        tmp=msg.decode()
        statu,content=json.loads(tmp)
        return message(statu,content)

    def show(self):
        print('statu: ',self.m[0],'; content: ',self.m[1])

class server(Process):
    def __init__(self,msg_list,host='localhost',port=50001):
        Process.__init__(self)
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.host=host
        self.port=port
        self.msg_list=msg_list
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
        
    def run(self):
        self.s.listen(5)
        while True:
            conn,addr=self.s.accept()
            #print('Connect with:',addr)
            data=conn.recv(512000)
            print("server recvd data:",data)
            statu,content=json.loads(data.decode()) 
            if statu<400 or statu>=500:
                msg=message(statu,content)
                self.msg_list.put(msg.msg_encode())
                conn.send(message(669,'recved').msg_encode())
            else:
                print("Testing msg recvd:",statu,content)
            
class messager(Process):
    def __init__(self,msg_list,host='locahost',debug=False):
        super().__init__()
        print("init the sender...")
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

def send_to(msg,host='localhost',port=50001):
    client=socket.socket()
    addr=(host,port)
    client.connect(addr)
    content=msg.msg_encode()
    client.send(content)
    recv=client.recv(512000)
    statu,content=json.loads(recv.decode())
    recv_msg=message(statu,content)
    #recv_msg.show()
    client.close()
    return recv_msg

# class flib_base:
#     def __init__(self,dct):
#         self.route=dct
#         #self.funcs=[]

#     def get_by_statu(self,statu):
#         if statu in self.route:
#             return self.route[statu]
#         else:
#             return self.not_exist_func

#     def regist_by_statu(self,func,statu=0):
#         #self.funcs.append(func)
#         if statu==0:
#             tmp=func.statu
#         else:
#             tmp=statu
#         self.route[tmp]=func

#     def not_exist_func(self):
#         print("This statu is not exist.")

#     def show_all(self):
#         print("%5s   %15s"%("statu","function name"))
#         for i in self.route:
#             print("%5d,   %15s"%(i,self.route[i].name))

# class func:
#     def __init__(self,statu,f,name=None, discription='This is the discrp of the function'):
#         self.statu=statu
#         self.discrp=discription
#         self.f=f
#         if name==None:
#             self.name="Noname_on_%d"%statu
#         else:
#             self.name=name

#     def run(self,msg):
#         return self.f(msg)

#     def help(self):
#         print("func : %s"%self.name)
#         print(self.discrp)    

class handler:
    def __init__(self,config='handler_config.json'):
        with open(config,'r') as ff:
            self.statu_to_func=json.loads(ff.read())['statu_to_func']
        
    def get_func(self,statu):
        func_name=self.statu_to_func[str(statu)]
        return eval("fl.%s"%func_name)


class worker(Process):
    def __init__(self,recv_list,send_list,hdlr=None):
        super().__init__()
        self.handler=hdlr
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
                work=self.handler.get_func(new_msg.statu)
                processed_msg=work(new_msg.content)
                self.send_or_remain(processed_msg)

    def send_or_remain(self,msg):
        statu=msg.statu
        if statu>10000:
            self.send_list.put(msg)
        else:
            self.recv_list.put(msg)
        
class micro_service(Process):
    def __init__(self,recv_list,send_list,wkr,*args):
        super().__init__()
        self.recv_list=recv_list
        self.send_list=send_list
        self.args=args
        self.route=dict()
        self.server=server(self.recv_list,host='localhost',port=50001)
        self.messager=messager(self.send_list,host='localhost')
        self.worker=worker(self.recv_list,self.send_list,wkr)

    def put_to_send_list(self,port,msg):
        new_msg=message(port,msg).msg_encode()
        self.send_list.put(new_msg)

    def put_to_recv_list(self,msg):
        new_msg=msg.msg_encode()
        self.recv_list.put(new_msg)
        

    def run(self):
        pass




# if __name__=="__main__":
#     msgl=multiprocessing.Queue()

#     s=server(msgl)
#     s.start()
#     print("Server started.")
