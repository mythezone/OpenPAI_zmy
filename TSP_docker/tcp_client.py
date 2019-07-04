import socket
import os,sys
import hashlib

class client:
    def __init__(self,addr,port,work_path):
        self.address=(addr,port)
        self.work_path=work_path
        self.tcp_client=socket.socket()

        