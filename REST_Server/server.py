import socket

s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind(('localhost',5001))
s.listen(10)
while True:
    conn,_=s.accept()
    data=conn.recv(8192)
    print(data.decode())
    conn.send("hello,world".encode())
    conn.close()