import socket
import sys,os
import hashlib

class servier:
    def __init__(self,addr,port,work_path):
        self.address=(addr,port)
        self.work_path=work_path
        self.tcp_servier=socket.socket()
        self.tcp_servier.bind(self.address)
        self.node_list=dict()
        
        

if __name__=="__main__":
    s=servier("localhost",6969,'./work')
    s.tcp_servier.listen(5)

    while True:
        conn,addr=s.tcp_servier.accept()
        print("conn:",conn,"\naddr:",addr)
        while True:
            data=conn.recv(2048)
            if not data:
                print("disconnected!")
                break
            
            print("Recieved cmd:",data.decode("utf-8"))
            cmd,filename=data.decode("utf-8").split(" ")
            if cmd=='get':
                if os.path.isfile(filename):
                    size=os.stat(filename).st_size
                    conn.send(str(size).encode("utf-8"))
                    print("size:",size)

                    conn.recv(1024)

                    m=hashlib.md5()
                    f=open(filename,'rb')
                    for line in f:
                        conn.send(line)
                        m.update(line)
                    f.close()

                    md5=m.hexdigest()
                    conn.send(md5.encode("utf-8"))
                    print("md5:",md5)


    s.tcp_servier.close()



