import numpy
import json
from functools import partial
import multiprocessing
import custom_func as cf

class message:
    def __init__(self,statu,content):
        self.statu=statu
        self.content=content
        self.m=[statu,content]

    def msg_encode(self):
        #return str(self.m).encode()
        msg=json.dumps(self.m).encode()
        return msg

    #@staticmethod
    def msg_decode(self,msg):
        statu,content=json.loads(msg.decode())
        if statu==901:
            return content
        elif statu==902:
            return content
        else:
            print("check your msg type!")
        return content

    @staticmethod
    def b2m(msg):
        """
        a static method of the class message,used to change the binary message recvd from the socket into a message class entity.
        """
        try:
            tmp=msg.decode()
        except:
            tmp=msg
        statu,content=json.loads(tmp)
        return message(statu,content)

    def show(self):
        print('statu: ',self.m[0],'; content: ',self.m[1])

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
        print("func registed succ.")

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
        self.regist_by_statu(func(102,partial(self.port_registry_respons,ob=ob),discription="Port registry response."))
        self.regist_by_statu(func(103,partial(self.port_request,ob=ob),discription="Port request."))
        self.regist_by_statu(func(104,partial(self.get_port_all,ob=ob),discription="get all ports."))
        self.regist_by_statu(func(105,partial(self.get_port_spec,ob=ob),discription="Get the spec port."))
        self.regist_by_statu(func(140,partial(self.port_not_found,ob=ob),discription="Port request."))
        self.debug=ob.debug
        self.ob=ob
   
    @staticmethod
    def port_registry(content,ob=None):
        '''
        Statu:101
        '''
        ob.route[content[0]]=content[1]
        new_msg=[102,'Registry succed.']
        ob.put_to_send_list(content[1],new_msg)
        ob.show_debug("Registry successed.")

    @staticmethod
    def port_registry_respons(content,ob=None):
        '''
        Statu:102
        '''
        print("Statu 102",content)

    @staticmethod
    def port_request(content,ob=None):
        '''
        Statu:103
        '''
        if content[1].lower()=='all':
            new_msg=[104,ob.route]
            ob.put_to_send_list(content[0],new_msg)
            ob.show_debug("ports send succefully.")
        else:
            if content[1] in ob.route:
                tmp=ob.route[content[1]]
                new_msg=[105,[tmp,content[1]]]
                ob.put_to_send_list(content[0],new_msg)
                ob.show_debug("port send successfully.")
            else:
                new_msg=[140,'port not found.']
                ob.put_to_send_list(content[0],new_msg)
                ob.show_debug("port not found.")

    @staticmethod
    def get_port_all(content,ob=None):
        '''
        Statu:104
        '''
        for i in content:
            ob.route[i]=content[i]
        ob.show_debug(ob.route)

    @staticmethod
    def get_port_spec(content,ob=None):
        '''
        Statu:105
        '''
        ob.route[content[0]]=content[1]
        ob.show_debug("the spec info has been added into the route.")

    @staticmethod
    def port_not_found(content,ob=None):
        '''
        Statu:140
        '''
        ob.show_debug('statu 140: port not found.')



class cstm_flib(std_flib):
    def __init__(self,dct,ob=None):
        super().__init__(ob=ob)
        for i in dct:
            self.regist_by_statu(func(i,partial(dct[i],ob=ob),discription='This is a custom function.'))
            



# #test class
class test:
    def __init__(self):
        self.route=dict()
        self.dct=dict()
        self.send_list=multiprocessing.Queue()
        self.dct=cf.profile().d
        self.s=cstm_flib(self.dct,ob=self)
        
    def t(self,msg):
        return self.s.get_by_statu(msg.statu)

if __name__=="__main__":
    t=test()
    s=t.s
    f=t.t(message(101,'test1'))
    f.run(['name',50001])
    print(s.route)
    print(t.route)