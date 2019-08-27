import json
from threading import Thread,Lock
import socket
import numpy as np 
import multiprocessing
from multiprocessing import Process,Manager 
import hashlib
import sys,os,time


def wait_message(wait_list,statu):
    while True:
        if wait_list.empty():
            time.sleep(5)
        else:
            msg=wait_list.get()
            new_msg=message.b2m(msg)
            _statu,content=new_msg.statu,new_msg.content
            if _statu==statu:
                return content
            else:
                wait_list.put(msg)

def wait_file(path,name):
    while True:
        ff=os.listdir(path)
        if name in ff:
            return path+name
        else:
            time.sleep(1)
            continue

def read_json(file_path):
    with open(file_path,'r') as f:
        temp=json.loads(f.read())
        return temp

class message:
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
        new_msg=json.loads(msg.decode())
        return new_msg

    @staticmethod
    def b2m(msg):
        """
        a static method of the class message,used to change the binary message recvd from the socket into a message class entity.
        """
        try:
            tmp=msg.decode()
        except:
            tmp=msg
        statu,content=json.loads(tmp)
        return message(statu,content)

    def show(self):
        print('statu: ',self.m[0],'; content: ',self.m[1])

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
        print("start")
        while True:
            conn,_addr=self.s.accept()
            #print('Connect with:',addr)
            data=conn.recv(51200)
            print("server recvd data:",data)
            msg=data
            statu,content=json.loads(data.decode())
            if statu==101:
                #port register
                print("The registry msg 101 is:",content)
                self.recv_list.put(msg)

            elif statu==102:
                _name,file_name,file_path=content
                new_name=file_name
                filename=file_path+new_name #+"new"
                f=open(filename,'w+b')
                recvd_size=0
                m=hashlib.md5()

                conn.send('wait for size...'.encode())
                respon=conn.recv(1024)
                print("respon:",respon)
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
                    #print("\r recvd:",int(recvd_size/file_size*100),"%")
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
            elif statu==444:
                #print("message recvd:",statu,content)
                conn.send(message(444,'recved').msg_encode())
                continue
            elif statu<400 or statu>=500:
                self.recv_list.put(msg)
                conn.send(message(466,'recved').msg_encode())
                #print("message recvd:",statu,content)
            else:
                print("Testing msg recvd:",statu,content) 

class messager(Process):
    def __init__(self,recv_list,send_list,host='localhost',name='master',debug=False):
        Process.__init__(self)
        print("Messager initiated.")
        self.send_list=send_list
        self.host=host
        self.debug=debug
        self.name=name

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
                    _next_port,file_name,file_path=content

                    if self.name=='master':
                        _port=_next_port
                    else:
                        _port=50001
                    addr=('localhost',_port)
                    s.connect(addr)

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
                addr=('localhost',next_port)
                #print("addr:",addr)
                s.connect(addr)
                s.send(new_msg)
                recv=s.recv(1024)
                #print(recv)
                s.close()

if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()
    ser=server(recv_list,send_list)

    ser.run()
    


