import socket
import os,sys
import hashlib

class client:
    def __init__(self,addr,port,work_path):
        self.address=(addr,port)
        self.work_path=work_path
        self.tcp_client=socket.socket()



if __name__=="__main__":
    s=client('localhost',6969,'./work')
    s.tcp_client.connect(s.address)
    print(s.tcp_client.recv(1024))
    s.tcp_client.close()