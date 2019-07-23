from base import *
from multiprocessing import Process
import multiprocessing
import json
import time
import create as cr
from additional_args import get_args

class worker_work(Process):
    def __init__(self, msg_list, server_ip, server_port, master_ip, master_port):
        Process.__init__(self)
        self.msg_list=msg_list
        self.server_ip = server_ip
        self.server_port = server_port
        self.master_ip = master_ip
        self.master_port = master_port

    def process(self,msg):
        statu,content=json.loads(msg.decode())
        new_msg=message(statu,content)
        return new_msg

    def init_problem(self,cities=20):
        cities=cr.create_cities(cities)
        content=cities.tolist()
        return content

    def run(self):
        print("The handle of the message has been started!")
        while True:
            if self.msg_list.empty():
                time.sleep(2)
                continue
            else:
                msg=self.msg_list.get()
                #print(msg)
                new_msg=self.process(msg)
                if new_msg.statu==666:
                    #print(new_msg.content)
                    content=self.init_problem()
                    msg=message(0,content)
                    while True:
                        count=0
                        try:
                            send_to(msg, host=new_msg.content[0], port=new_msg.content[1])
                            break
                        except:
                            time.sleep(2)
                            count+=1
                            if count==10:
                                print("Try 10 times the server is not ready.Please check the port of the server.")
                                break

                elif new_msg.statu==669:
                    print(new_msg.content)
                    
                    msg=message(1, [self.server_ip, self.server_port])
                    send_to(msg)
                elif new_msg.statu==444:
                    #port for test
                    print("Test:",new_msg.content)
                elif new_msg.statu==0:
                    print(new_msg.content)
                else:
                    print("something wrong! error %d"%new_msg.statu,new_msg.content)
                
class worker:
    def __init__(self,name="loop", ip='localhost', port=0, master_ip='localhost', master_port=50001):
        self.msg_list=multiprocessing.Queue()
        self.ip = ip 
        self.port = port
        while True:
            try:
                if self.port == 0: 
                  self.port=np.random.randint(50010,60000)
                self.server = server(self.msg_list, host=self.ip, port=self.port)
                self.server.start()
                print("Server started......")
                msg=message(101,[name, self.ip, self.port])
                send_to(msg, master_ip, master_port)
                break
            except:
                print("Warning: connection to the master failed!")
                time.sleep(5)
                continue
                
        self.master_work = worker_work(self.msg_list, self.ip, self.port, master_ip, master_port)

    def run(self):
        self.master_work.start()

if __name__=='__main__':
    args = get_args()
    master_ip = args.master_ip_list.split(',')[0]#Suppose there is only one master
    master_port = int(args.master_port_list.split(',')[0])
    worker_ip_list = args.worker_ip_list.split(',')
    worker_port_list = [int(x) for x in args.worker_port_list.split(',')]
    task_role_index = args.task_role_index

    time.sleep(60)# in case of this program and the master are starting before other two
    m=worker(name='init', ip=worker_ip_list[task_role_index], port=worker_port_list[task_role_index], master_ip=master_ip, master_port=master_port)
    m.run()
