import time

class user:
    def __init__(self,name,pwd,group=None):
        self.name=name
        self.pwd=pwd
        self.group=group


class data_info:
    def __init__(self,name,size,date,path):
        self.name=name
        self.size=size
        self.date=date
        self.path=path

    def show_info(self):
        res=''
        res+='name:%s, '%self.name
        res+='size:%s, '%self.size
        res+='date:%s, '%self.date
        res+='path:%s'%self.path
        return res

class model_info:
    def __init__(self,name,size,date,path):
        self.name=name
        self.size=size
        self.date=date
        self.path=path

    def show_info(self):
        res=''
        res+='name:%s, '%self.name
        res+='size:%s, '%self.size
        res+='date:%s, '%self.date
        res+='path:%s'%self.path
        return res

class task_info:
    def __init__(self,name,id,config_id,statu):
        self.name=name
        self.id=id
        self.config_id=config_id
        self.statu=statu
        self.log=list()
        self.add_log("task created.")
        self.start_time=time.time()

    def show_info(self):
        res='Task name:%s,id:%d,statu:%s'%(self.name,self.id,self.statu)
        return res

    def add_log(self,st):
        self.log.append(st)

    def show_log(self):
        res=''
        for l in self.log:
            res+=l+'<Br/>'
        return res


class cluster_info:
    def __init__(self,name,percent):
        self.name=name
        self.percent=percent
        
        

    def show_info(self):
        res='cluster name:%s,used:%.2f'%(self.name,self.percent)
        return res

    
