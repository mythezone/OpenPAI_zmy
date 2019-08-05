from flask import Flask
from base_class import *

app=Flask(__name__)

# @app.route('/')
# def hello_world():
#     return "Hello,world!"

@app.route('/k')
def other():
    return "recvd a word"

def hello_world():
    return 'hello world'
app.add_url_rule('/hello', 'hello', hello_world)


#集群登陆，前端配置
@app.route('/user/config/<name>/<passwd>')
def login(name,passwd):
    return "user:%s,pwd:%s"%(name,passwd)

#提交数据-查询数据
t=data_info('test.txt','5m','2019.8.4','./')

data_list=list()
data_index=list()
model_list=list()
model_index=list()
data_list.append(t)
data_list.append(t)
model_list.append(t)

data_index.append(t.name)
model_index.append(t.name)


@app.route('/user/ask/upload/history/data')
def ask_data():
    res=''
    for i in data_list:
        res+=i.show_info()+'\r\n'
    return res
        



@app.route('/user/ask/upload/history/<data>')
def search_data(data):
    if data in data_index:
        i=data_index.index(data)
        tmp=data_list[i]
        return tmp.show_info()
    else:
        return "file not found."


#提交数据-查询模型
@app.route('/user/ask/upload/history/model')
def ask_model():
    res=''
    for i in model_list:
        res+=i.show_info()+'\r\n'
    return res


#提交数据-上传
@app.route('/user/upload/data/<path>')
def upload_data(path):
    pass

@app.route('/user/upload/model/<path>')
def upload_model(path):
    pass

@app.route('/user/upload/resume/<checkpoint_id>')
def resume_checkpoint(checkpoint_id):
    pass

@app.route('/user/upload/config/<path>')
def upload_config(path):
    pass

#开始，终止运行
@app.route('/user/command/start/<id>')
def start_id(id):
    pass

@app.route('/user/command/stop/<id>')
def stop_id(id):
    pass

#查看集群任务进度
@app.route('/user/ask/cluster_info')
def cluster_info():
    pass

@app.route('/user/ask/task')
def task_info():
    pass

@app.route('/user/ask/running_task')
def running_task():
    pass

@app.route('/user/ask/log/<task_id>')
def task_log(task_id):
    pass

if __name__=="__main__":
    #app.run(host, port, debug, options)
    app.run(debug=True)