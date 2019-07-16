from base import *



if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()

    ms=micro_service(recv_list,send_list,name='init',port='s')
    ms.run()

