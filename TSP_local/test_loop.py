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
        self.next_port=0
        self.data=list()

    def process(self,msg):
        statu,content=json.loads(msg.decode())
        new_msg=message(statu,content)
        return new_msg

    # def init_problem(self,population=10,nodes=10,cities_num=100):
    #     self.population=population
    #     self.nodes=nodes
    #     self.num=cities_num
    #     cities=cr.create_cities(self.num)
    #     content=cities.tolist()
    #     return content

    def init_distance(self,cities,population=10,nodes=10):
        self.num=len(cities)
        self.population=population
        self.nodes=nodes
        cities=np.array(cities)
        self.dist=cr.distance_matrix(cities)
        #dist=dist.tolist()
        self.count=0
        self.result=[]
        return self.dist

    def init_solutions(self):
        routes=cr.init_solutions(self.population,self.num)
        return routes

    def run(self):
        print("The handle of the message has been started!")
        while True:
            if self.msg_list.empty():
                time.sleep(2)
                continue
            else:
                msg=self.msg_list.get()
                
                new_msg=self.process(msg)

                if new_msg.statu==0:
                    print(new_msg.content)
                    self.data=new_msg.content
                    self.dist=self.init_distance(self.data)                        
                    msg=message(2,self.server_port)
                    send_to(msg)

                elif new_msg.statu==1:
                    send_to(message(2,new_msg.content),port=self.next_port)
                elif new_msg.statu==444:
                    #print("test content:",new_msg.content)
                    pass
                elif new_msg.statu==669:
                    print("new_msg.content: ",new_msg.content)
                elif new_msg.statu==666:
                    self.next_port=new_msg.content
                    msg=message(444,'your message has been processed.')
                    send_to(msg,port=self.next_port)
                    dist_msg=message(801,self.dist)

                    send_to(dist_msg,port=self.next_port)

                    for i in range(self.nodes):
                        solutions=self.init_solutions()
                        #print('solutions:',solutions)
                        msg=message(1,solutions).msg_encode()
                        self.msg_list.put(msg)

                elif new_msg.statu==700:
                    print('a final result rcvd.')
                    self.count+=1
                    self.result.append(new_msg.content)
                    if self.count==self.nodes:
                        sorted_solution=sorted(solutions,key=lambda x:cr.cost(x,self.dist))[0]
                        print("final result is:",sorted_solution)
                        print("least cost is :",cr.cost(sorted_solution,self.dist))
                else:
                    print("something wrong! error %d"%new_msg.statu,new_msg.content)
                

class worker:
    def __init__(self,name="loop",host='localhost'):
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
                break
                
        self.master_work=worker_work(self.msg_list,self.port)

    def run(self):
        self.master_work.start()


if __name__=='__main__':
    m=worker(name='loop')
    m.run()