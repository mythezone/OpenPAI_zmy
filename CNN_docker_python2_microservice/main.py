import socket
from base import *



if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()

    mgr=messager(recv_list,send_list,name='main')

    mgr.start()

    #msg=message(102,[32,'ncs.py','./']).msg_encode()
    msg=message(2,'start').msg_encode()
    send_list.put(msg)




    # s=socket.socket()
    # addr=('localhost',50001)
    # s.connect(addr)
    # msg=message(102,[32,'ncs.py','./']).msg_encode()
    # s.send(msg)
    # r=s.recv(1024)
    # print(r.decode())
    # s.close()
