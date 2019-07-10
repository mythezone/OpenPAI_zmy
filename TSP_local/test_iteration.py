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
        self.matrix=[]
        self.get_next_port_flag=True
        

    def process(self,msg):
        statu,content=eval(msg.decode())
        new_msg=message(statu,content)
        return new_msg

    # def init_problem(self,population=10,nodes=10,cities_num=100):
    #     self.population=population
    #     self.nodes=nodes
    #     self.num=cities_num
    #     cities=cr.create_cities(self.num)
    #     content=cities.tolist()
    #     return content

    # def init_distance(self,cities,population=10,nodes=10):
    #     self.num=len(cities)
    #     self.population=population
    #     self.nodes=nodes
    #     cities=np.array(cities)
    #     dist=cr.distance_matrix(cities)
    #     dist=dist.tolist()
    #     return dist

    # def init_solutions(self):
    #     routes=cr.init_solutions(self.population,self.num)
    #     return routes

    def iteration(self,solutions,matrix,max_iteration=100,max_time=180):
        start=time.time()
        time_escaped=0
        iter=0
        while iter<max_iteration and time_escaped<max_time:
            solutions=cr.next_generation(solutions,matrix)
            iter+=1
            time_escaped=time.time()-start
        return solutions[0].tolist()
        

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
                    pass

                elif new_msg.statu==1:
                    send_to(message(444,new_msg.content),port=self.next_port)
                
                elif new_msg.statu==2:
                    # print(new_msg.content)
                    solutions=np.array(new_msg.content)
                    solution=self.iteration(solutions,self.matrix)
                    print("best solution found in this node:",solution)
                    msg=message(802,solution)
                    self.msg_list.put(msg.msg_encode())

                    
                    if self.get_next_port_flag:
                        print("get next port")
                        msg=message(1,self.server_port)
                        send_to(msg)
                        self.get_next_port_flag=False
                    

                elif new_msg.statu==444:
                    print("your test msg recvd.")

                elif new_msg.statu==666:
                    self.next_port=new_msg.content
                    #print("next port is:",self.next_port)
                    msg=message(444,'your message has been processed.')
                    send_to(msg,port=self.next_port)
                    
                elif new_msg.statu==669:
                    print("new_msg.content: ",new_msg.content)
                    

                elif new_msg.statu==801:
                    print('the distance matrix recived.')
                    self.matrix=np.array(new_msg.content)

                elif new_msg.statu==802:
                    #print("ready to send a best solution!")
                    if self.next_port==0:
                        self.msg_list.put(msg)
                        continue
                    else:
                        msg=message(700,new_msg.content)
                        send_to(msg,port=self.next_port)
                    

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
                pass
        self.master_work=worker_work(self.msg_list,self.port)

    def run(self):
        self.master_work.start()


if __name__=='__main__':
    m=worker(name='iteration')
    m.run()