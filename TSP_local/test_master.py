from base import *
from multiprocessing import Process
import multiprocessing
import json
import time
from array import array


class master_work(Process):
    def __init__(self,msg_list,jobconfig_path='task_config.json'):
        Process.__init__(self)
        with open(jobconfig_path,'r') as f:
            self.job_config=json.loads(f.read())
            self.algo=self.job_config['process']
        self.route=dict()
        self.msg_list=msg_list

    def next_port(self,statu):
        name=self.algo[str(statu)]
        try:
            port=self.route[name]
            return port
        except:
            print("The port has not been registed!")
        # show_flag=True
        # while True:
        #     if name in self.route:
        #         port=self.route[name]
        #         break
        #     else:
        #         time.sleep(2)
        #         if show_flag:
        #             print("The server has not be registed!Plz wait!")
        #             show_flag=False

       

    def process(self,msg):
        statu,content=json.loads(msg)
        if statu==101:
            self.route[content[0]]=content[1]
            new_msg=message(669,'Port %d registed successfully!'%content[1])
            send_to(new_msg,port=content[1])
            return new_msg
        else:
            port=self.next_port(statu)
            new_msg=message(666,port)
            send_to(new_msg,port=content)
            return new_msg
            

    def run(self):
        print("The handle of the message has been started!")
        while True:
            if self.msg_list.empty():
                time.sleep(2)
                continue
            else:
                msg=self.msg_list.get()
                print(msg)
                new_msg=self.process(msg)
                new_msg.show()

class master:
    def __init__(self,host='localhost',port=50001):
        self.msg_list=multiprocessing.Queue()
        
        self.server=server(self.msg_list,host=host,port=port)
        self.master_work=master_work(self.msg_list)

    def run(self):
        self.server.start()
        self.master_work.start()

if __name__=='__main__':
    m=master()
    m.run()