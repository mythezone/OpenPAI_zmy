from base import *
from test_custom_func import  get_dct
from func_lib import message



if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()
    d=get_dct()

    ms=micro_service(recv_list,send_list,func_dct=d,name='init',port='s')
    ms.run()
    ms.recv_list.put(message(0,11).msg_encode())
    print("msg put into the recv list.")

