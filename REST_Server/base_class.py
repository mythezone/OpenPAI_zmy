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