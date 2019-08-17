from base import *
from test_custom_func import  get_dct
from multiprocessing import Process,Manager

ports=dict({
    'master':50000,
    'init':50001,
    'main':50002,
    'loop1':50003,
    'loop2':50004,
    'evaluation':50005

})

algo=dict({
    0:'master',
    1:'init',
    2:'main',
    3:'loop1',
    4:'loop2',
    5:'evaluation',
    51:'evaluation',
    52:'evalutaion',
    53:'evaluation'
})

class master_worker(Process):
    def __init__(self,recv_list,send_list,host='localhost',debug=True):
        Process.__init__(self)
        
        self.send_list=send_list
        self.recv_list=recv_list
        self.debug=debug
        self.host=host

    def run(self):
        print("worker started to work.")
        while True:
            if self.recv_list.empty():
                time.sleep(1)
                continue
            else:
                msg=self.recv_list.get()
                statu,content=json.loads(msg.decode())
                if statu not in algo:
                    print('wrong statu %d'%statu)
                    continue
                else:
                    next_server_name=algo[statu]
                    if next_server_name not in ports:
                        print("port not registed,please wait...")
                        self.recv_list.put(msg)
                        time.sleep(1)
                        continue
                    else:
                        next_server_port=ports[next_server_name]
                        new_msg=message(next_server_port,[statu,content]).msg_encode()
                        self.send_list.put(new_msg)
                        if self.debug:
                            print(content,' has been transmited.')

if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()

    ser=server(recv_list,send_list)
    msg=messager(recv_list,send_list)
    wrk=master_worker(recv_list,send_list)

    ser.start()
    msg.start()
    wrk.start()

    print("main program over.")