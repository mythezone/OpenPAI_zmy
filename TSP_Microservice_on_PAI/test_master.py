from base import *
from multiprocessing import Process
import multiprocessing
import json
import time
from additional_args import get_args
from log import generate_log_func

log_info = generate_log_func('file', 'master.txt')

class master_work(Process):
    def __init__(self,msg_list,jobconfig_path='task_config.json'):
        Process.__init__(self)
        with open(jobconfig_path,'r') as f:
            self.job_config=json.loads(f.read())
            self.algo=self.job_config['process']
        self.route_ip=dict()
        self.route_port=dict()
        self.msg_list=msg_list

    def next_port(self,statu):
        name=self.algo[str(statu)]
        try:
            ip=self.route_ip[name]
            port=self.route_port[name]
            return ip,port
        except:
            log_info("The ip or the port has not been registed!")    

    def process(self,msg):

        statu,content=json.loads(msg)
        if statu==101:
            self.route_ip[content[0]]=content[1]
            self.route_port[content[0]]=content[2]
            new_msg=message(669,'IP %s with Port %d registed successfully!'%(content[1], content[2]))
            send_to(new_msg, host=content[1], port=content[2])
            return new_msg
        else:
            ip, port = self.next_port(statu)
            new_msg=message(666,[ip, port])
            send_to(new_msg, host=content[0], port=content[1])
            return new_msg
            

    def run(self):
        log_info("The handle of the message has been started!")
        while True:
            if self.msg_list.empty():
                time.sleep(2)
                continue
            else:
                msg=self.msg_list.get()
                log_info(msg)
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
    args = get_args()
    master_ip = args.master_ip_list.split(',')[0]#Suppose there is only one master
    master_port = int(args.master_port_list.split(',')[0])
    m=master(host=master_ip, port=master_port)
    m.run()
