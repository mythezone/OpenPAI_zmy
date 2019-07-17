from base import *
from test_custom_func import  get_dct
from multiprocessing import Process,Manager




if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()
    route=dict()
    
    ms=micro_service(recv_list,send_list,route)
    ms.run()