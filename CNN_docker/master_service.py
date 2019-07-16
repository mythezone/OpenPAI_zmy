from base import *
from test_custom_func import  get_dct



if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()
    d=get_dct()

    ms=micro_service(recv_list,send_list,func_dct=d,name='master')
    ms.run()