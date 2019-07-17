from threading import Thread,Lock
import socket
import numpy as np
import sys,os,time
from io import BytesIO
import base64
import json
import multiprocessing
from multiprocessing import Process,Manager
import func_lib as fl
from func_lib import message
import hashlib
#import custom_func as cf


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
            if statu==905:
                file_name,file_path=content
                if os.path.isfile(file_path+file_name):
                    size=os.stat(file_path+file_name).st_size
                    conn.send(str(size).encode())

                    conn.recv(1024)

                    m=hashlib.md5()
                    f=open(file_path+file_name,'rb')
                    for line in f:
                        conn.send(line)
                        m.update(line)
                    f.close()

                    md5=m.hexdigest()
                    conn.send(md5.encode())
                    print("md5:",md5)
                else:
                    conn.send("file you needed is not found.")
                    print("file not found...")
            elif statu==907:
                new_msg=message(904,content)
                self.send_list.put(new_msg.msg_encode())

            elif statu<400 or statu>=500:
                
                msg=message(statu,content)
                self.recv_list.put(msg.msg_encode())
                conn.send(message(466,'recved').msg_encode())
                
            else:
                print("Testing msg recvd:",statu,content)
            
class messager(Process):
    def __init__(self,ob=None,host='locahost',debug=False):
        super().__init__()
        print("Messager initiated.")
        #self.s=socket.socket()
        self.ob=ob
        self.send_list=self.ob.send_list
        self.route=self.ob.route
        self.algo_route=self.ob.algo_route
        self.host=host
        self.debug=debug
        self.port=self.ob.server.port
        self.name=ob.name

    def run(self):
        while True:
            if self.send_list.empty():
                time.sleep(2)
                continue
            else:
                # self.route=self.ob.route
                msg=self.send_list.get()
                statu,content=json.loads(msg.decode())
                if statu<100:
                    if statu in self.algo_route:
                        next_name=self.algo_route[statu]
                        if next_name in self.ob.route:
                            next_port=self.ob.route[next_name] 
                        else:
                            print('Try to get the needed port.',statu,content)
                            if self.name=='master':
                                self.send_list.put(msg)
                                time.sleep(4)
                                continue
                            new_msg=message(102,[self.port,next_name])
                            self.send_list.put(new_msg.msg_encode)
                            print("waiting the port respons")
                            self.send_list.put(msg)
                            continue
                    else:
                        print("This statu is not defined in the algorithm, plz check.")
                        print("Error info:",statu,content)
                        continue
                elif 100<=statu<200:
                    #message with statu in this range will be send to the master server.
                    next_port=50001
                elif 400<=statu<500:
                    print("Test or Info msg:",statu,content)
                elif statu==904:
                    '''
                    message(904,[server_name,file_name])
                    request for a file from server with file name.
                    '''
                    next_name,file_name,file_path=content
                    if next_name in self.ob.route:
                        next_port=self.ob.route[next_name] 
                    else:
                        print("Now the route is :",self.ob.route)
                        print('Try to get the needed port.',statu,content)
                        if self.name=='master':
                            self.send_list.put(msg)
                            time.sleep(4)
                            continue
                        new_msg=message(102,[self.port,next_name])
                        self.send_list.put(new_msg.msg_encode)
                        print("waiting the port respons")
                        self.send_list.put(msg)
                        continue

                    self.s=socket.socket()
                    self.s.connect((self.host,next_port))
                    self.s.send(message(905,[file_name,file_path]).msg_encode())
                    server_respons=self.s.recv(1024)

                    try:
                        file_size=int(server_respons.decode())
                    except:
                        print(server_respons.decode())
                        continue

                    print("recvd size:",file_size)

                    self.s.send("ready for recv file....".encode())
                    filename=file_path+"new_"+file_name
                    f=open(filename,'wb')
                    recvd_size=0
                    m=hashlib.md5()

                    while recvd_size<file_size:
                        size=0
                        if file_size-recvd_size>1024:
                            size=1024
                        else:
                            size=file_size-recvd_size
                        data=self.s.recv(size)
                        data_len=len(data)
                        recvd_size+=data_len
                        print("\r\n  recvd:",int(recvd_size/file_size*100),"%")
                        m.update(data)
                        f.write(data)
                    
                    print("real recvd size:",recvd_size)
                    md5_server=self.s.recv(1024).decode()
                    md5_client=m.hexdigest()
                    print("md5 on service:",md5_server)
                    print("md5 on client:",md5_client)
                    if md5_client==md5_server:
                        print("sending success.")
                        self.s.close()
                        continue
                    else:
                        print("sending fail.preparad for next try....")
                        self.send_list.put(msg)
                        self.s.close()
                        continue

                elif statu==906:
                    next_name,file_name,file_path=content
                    if next_name in self.ob.route:
                        next_port=self.ob.route[next_name]
                    else:
                        print('Try to get the needed port.',statu,content)
                        if self.name=='master':
                            self.send_list.put(msg)
                            time.sleep(4)
                            continue

                        new_msg=message(102,[self.port,next_name])
                        self.send_list.put(new_msg.msg_encode)
                        print("waiting the port respons")
                        self.send_list.put(msg)
                        continue

                    new_msg=message(907,[self.name,file_name,file_path]).msg_encode()
                    self.s=socket.socket()
                    addr=(self.host,next_port)
                    self.s.connect(addr)
                    self.s.send(new_msg)
                    recv=self.s.recv(52000)
                    print(recv)
                    self.s.close()
                    

                elif statu>10000:
                    next_port=statu
                else:
                    print("error :wrong statu ",statu)
                    continue

                self.s=socket.socket()
                addr=(self.host,next_port)
                self.s.connect(addr)
                new_msg=message(content[0],content[1]).msg_encode()
                self.s.send(new_msg)
                recv=self.s.recv(52000)
                print(recv)
                self.s.close()
                    

class worker(Process):
    def __init__(self,ob=None,custom_func=dict()):
        super().__init__()
        self.flib=fl.cstm_flib(custom_func,ob=ob)
        self.ob=ob
        self.recv_list=ob.recv_list
        self.send_list=ob.send_list
        
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
    def __init__(self,recv_list,send_list,route,*args,func_dct=dict(),\
        task_config='task_config.json',host='localhost',port=50001,\
            name='service_name',debug=True,**kargs):
        #super().__init__()
        self.recv_list=recv_list
        self.send_list=send_list
        self.args=args
        self.name=name
        self.kargs=kargs 
        self.route=route
        self.route['master']=50001
        self.debug=debug

        #statu to name.
        if task_config!='':
            with open(task_config,'r') as ff:
                tmp=json.loads(ff.read())
                self.help=tmp['comment']
                self.algo_route=tmp['algo_statu']
                self.commom_statu=tmp['commom_statu']
        else:
            self.help=dict()
            self.algo_route=dict()
            self.commom_statu=dict()

        self.dct=func_dct
        self.server=server(ob=self,host=host,port=port)
        self.messager=messager(ob=self,host=host)
        self.worker=worker(ob=self,custom_func=self.dct)

    def put_to_send_list(self,port,content):
        new_msg=message(port,content).msg_encode()
        self.send_list.put(new_msg)

    def show_debug(self,*args):
        if self.debug==True:
            for i in args:
                print(i)
        else:
            return

    def run(self):
        self.server.start()
        self.messager.start()
        self.worker.start()
        

if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()

    ms=micro_service(recv_list,send_list,dict())
    ms.run()
