from base import *
from test_custom_func import  get_dct
from func_lib import message



if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()
    route=dict()
    ms=micro_service(recv_list,send_list,route,name='init',port='s')
    ms.run()

    ms.send_list.put(message(102,[1,"test_file.dmg","./test_fold/"]).msg_encode())
    print("msg put into the recv list.")

