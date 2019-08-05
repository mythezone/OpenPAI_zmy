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
    def __init__(self,recv_list,send_list,name='master',host='localhost',port=50001):
        Process.__init__(self)
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.host=host
        self.port=port
        self.recv_list=recv_list
        self.send_list=send_list
        
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
            msg=data
            statu,content=json.loads(data.decode())
            if statu==101:
                #port register
                print("The registry msg 101 is:",content)
                self.recv_list.put(msg)

            elif statu==102:
                _,file_name,file_path=content
                filename=file_path+file_name+"new"
                f=open(filename,'wb')
                recvd_size=0
                m=hashlib.md5()

                conn.send('wait for size...'.encode())
                respon=conn.recv(1024)
                file_size=int(respon.decode())
                conn.send('Ready for recv...'.encode())
                while recvd_size<file_size:
                    size=0
                    if file_size-recvd_size>1024:
                        size=1024
                    else:
                        size=file_size-recvd_size

                    data=conn.recv(size)
                    data_len=len(data)
                    recvd_size+=data_len
                    print("\r recvd:",int(recvd_size/file_size*100),"%")
                    m.update(data)
                    f.write(data)

                f.close()
                print("real recvd size:",recvd_size)
                md5_s=conn.recv(1024).decode()
                md5_c=m.hexdigest()
                print("original md5:",md5_s)
                if md5_c==md5_s:
                    print("recv success.")
                    conn.send('s'.encode())
                else:
                    print("recv failure.")
                    conn.send('f'.encode())
                self.recv_list.put(msg)
                continue

            elif statu<400 or statu>=500:
                self.recv_list.put(msg)
                conn.send(message(466,'recved').msg_encode())
            else:
                print("Testing msg recvd:",statu,content)
            
class messager(Process):
    def __init__(self,recv_list,send_list,host='locahost',debug=False):
        super().__init__()
        print("Messager initiated.")
        self.send_list=send_list
        self.host=host
        self.debug=debug

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
                    next_port=50001
                    new_msg=msg
                elif statu==102:
                    s=socket.socket()
                    _,file_name,file_path=content
                    s.connect(('localhost',50001))
                    s.send(msg)
                    s_resp=s.recv(1024)
                    print(s_resp.decode())
                    file_size=os.stat(file_path+file_name).st_size
                    s.send(str(file_size).encode())
                    s_resp=s.recv(1024)
                    print(s_resp.decode())
                    f=open(file_path+file_name,'rb')
                    m=hashlib.md5()
                    for line in f:
                        s.send(line)
                        m.update(line)
                    f.close()

                    md5=m.hexdigest()
                    s.send(md5.encode())
                    print("md5:",md5)
                    print("sending over.")
                    flag=s.recv(1024).decode()
                    if flag=='s':
                        print("sending success.")
                    else:
                        self.send_list.put(msg)
                        print("sending fall,try again.")
                    s.close()
                    continue

                elif 400<=statu<500:
                    print("Test or Info msg:",statu,content)
                    continue        

                elif statu>10000:
                    next_port=statu
                    new_msg=message(content[0],content[1]).msg_encode()
                else:
                    print("error :wrong statu ",statu)
                    continue

                s=socket.socket()
                addr=(self.host,next_port)
                s.connect(addr)
                # new_msg=message(content[0],content[1]).msg_encode()
                s.send(new_msg)
                recv=s.recv(1024)
                print(recv)
                s.close()

class worker(Process):
    def __init__(self,recv_list,send_list,algo_route=dict(),work=lambda statu,content:print(statu,content)):
        super().__init__()
        #self.flib=fl.cstm_flib(custom_func,ob=ob)
        self.recv_list=recv_list
        self.send_list=send_list
        self.route=dict()
        self.algo_route=algo_route
        
    def run(self):
        while True:
            if self.recv_list.empty():
                time.sleep(2)
                #print("No msg in recvlist")
                continue
            else:
                
                msg=self.recv_list.get()
                print("There is a msg in recv_list",msg.decode())
                new_msg=message.b2m(msg)
                statu,content=new_msg.statu,new_msg.content
                if statu==101:
                    self.route[content[0]]=content[1]
                else:
                    if statu in self.algo_route:
                        next_name=self.algo_route[statu]
                        if next_name in self.route:
                            next_port=self.route[next_name]
                            send_msg=message(next_port,[msg.statu,msg.content]).msg_encode()
                            self.send_list.put(send_msg)
                        else:
                            self.recv_list.put(msg)
                            print("the port has not been registed ,please wait.")
                            time.sleep(2)

                    else:
                        #self.recv_list.put(msg)
                        print("the algo route is not exist.")
                    



class micro_service:
    def __init__(self,recv_list,send_list,route,*args,\
        task_config='task_config.json',host='localhost',port=50001,\
            name='master',debug=True,**kargs):
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

        self.server=server(self.recv_list,self.send_list,name=self.name,host=host,port=port)
        self.messager=messager(self.recv_list,self.send_list,host=host)
        self.worker=worker(self.recv_list,self.send_list,algo_route=self.algo_route)

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
