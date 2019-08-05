import sys,os
import socket
from urllib import parse,request


c=socket.socket(socket.AF_INET,socket.SOCK_STREAM)

textmod={'user':'admin','password':'admin'}
textmod = parse.urlencode(textmod)
header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'}

url='localhost:5000'
c.connect(('localhost',5001))
c.send("hello,im client".encode())
re=c.recv(1024)
print(re.decode())