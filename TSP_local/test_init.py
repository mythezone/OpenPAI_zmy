from base import *
from multiprocessing import Process
import multiprocessing
import json
import time
import create as cr



class worker_work(Process):
    def __init__(self,msg_list,server_port):
        Process.__init__(self)
        self.msg_list=msg_list
        self.server_port=server_port

    def process(self,msg):
        statu,content=json.loads(msg.decode())
        new_msg=message(statu,content)
        return new_msg

    def init_problem(self,cities=70):
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
                            send_to(msg,port=new_msg.content)
                            break
                        except:
                            time.sleep(2)
                            count+=1
                            if count==10:
                                print("Try 10 times the server is not ready.Please check the port of the server.")
                                break


                elif new_msg.statu==669:
                    print(new_msg.content)
                    
                    msg=message(1,self.server_port)
                    send_to(msg)
                elif new_msg.statu==444:
                    #port for test
                    print("Test:",new_msg.content)
                elif new_msg.statu==0:
                    print(new_msg.content)
                else:
                    print("something wrong! error %d"%new_msg.statu,new_msg.content)
                

class worker:
    def __init__(self,name="init",host='localhost'):
        self.msg_list=multiprocessing.Queue()
        while True:
            try:
                self.port=np.random.randint(50010,60000)
                self.server=server(self.msg_list,host=host,port=self.port)
                self.server.start()
                print("Server started......")
                msg=message(101,[name,self.port])
                send_to(msg)
                break
            except:
                pass
        self.master_work=worker_work(self.msg_list,self.port)

    def run(self):
        self.master_work.start()


if __name__=='__main__':
    m=worker()
    m.run()