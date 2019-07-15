import numpy
import json
from functools import partial
from base import message
import multiprocessing

class flib_base:
    def __init__(self):
        self.route=dict()
        #self.funcs=[]

    def get_by_statu(self,statu):
        if statu in self.route:
            return self.route[statu]
        else:
            return self.not_exist_func

    def regist_by_statu(self,func,statu=0):
        #self.funcs.append(func)
        if statu==0:
            tmp=func.statu
        else:
            tmp=statu
        self.route[tmp]=func

    def not_exist_func(self):
        print("This statu is not exist.")

    def show_all(self):
        print("%5s   %15s"%("statu","function name"))
        for i in self.route:
            print("%5d,   %15s"%(i,self.route[i].name))

class func:
    def __init__(self,statu,f, discription='This is the discrp of the function'):
        self.statu=statu
        self.discrp=discription
        self.f=f
        # if name==None:
        #     self.name="Noname_on_%d"%statu
        # else:
        #     self.name=name

    def run(self,content):
        return self.f(content)

    def help(self):
        #print("func : %s"%self.name)
        print(self.discrp)    


class std_flib(flib_base):
    def __init__(self,ob=None):
        super().__init__()
        self.regist_by_statu(func(101,partial(self.port_registry,ob=ob),discription='Port register.'))
        self.regist_by_statu(func(102,partial(self.port_request,ob=ob),discription="Port request."))

    @staticmethod
    def port_registry(msg,ob=None):
        ob.route[msg[0]]=msg[1]
        #print(ob.route)
        new_msg=message(401,'Registry succed.')
        ob.send_list.put(new_msg.msg_encode())

    @staticmethod
    def port_request(msg,ob=None):
        if msg[1].lower()=='all':
            new_msg=message(402,ob.route)
            ob.put_to_send_list(msg[0],new_msg)
            print("ports send succefully.")
        else:
            if msg[1] in ob.route:
                tmp=ob.route[msg[1]]
                new_msg=message(403,[tmp,msg[1]])
                ob.put_to_send_list(msg[0],new_msg)
                print("port send successfully.")
            else:
                new_msg=message(404,'port not found.')
                ob.put_to_send_list(msg[0],new_msg)
                print("port not found.")


class flib(std_flib):
    def __init__(self,dct,ob=None):
        super().__init__(ob=ob)
        for i in dct:
            self.route[i]=dct[i]



# #test class
class test:
    def __init__(self):
        self.route=dict()
        self.send_list=multiprocessing.Queue()
        self.route[400]=lambda x:x+10
        self.s=flib(self.route,ob=self)
        
    def t(self,msg):
        return self.s.get_by_statu(msg.statu)