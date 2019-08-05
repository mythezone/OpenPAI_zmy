from flask import Flask,render_template,request,redirect,url_for
from werkzeug import secure_filename
from base_class import *
import os,sys,time

app=Flask(__name__)

# @app.route('/')
# def hello_world():
#     return "Hello,world!"

@app.route('/')
def home_page():
    return render_template('index.html')

def hello_world():
    return 'hello world'
app.add_url_rule('/hello', 'hello', hello_world)


#集群登陆，前端配置
u=user('admin','123456')
users_list=list()
users_list.append(u)
users_name=list()
users_name.append(u.name)

@app.route('/user/login')
def login():
    return render_template('login.html')


@app.route('/user/config',methods=['POST','GET'])
def login_result():
    if request.method=='POST':
        user=request.form.to_dict()
        print(user)
        if user['name'] in users_name:
            i=users_name.index(user['name'])
            if users_list[i].pwd!=user['passwd']:
                return "Pwd wrong.try again."
            else:
                return "%s login."%user['name']
        else:
            return "user not found."


#提交数据-查询数据
t=data_info('test.txt','5m','2019.8.4','./')
ta=task_info('master',12312,123,'running')
data_list=list()
data_index=list()
model_list=list()
model_index=list()
task_list=list()
task_index=list()

data_list.append(t)
data_list.append(t)
model_list.append(t)
task_list.append(ta)
task_index.append(ta.id)

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
@app.route('/upload')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader',methods=['GET','POST'])
def upload_file1():
    if request.method=='POST':
        f=request.files['file']
        f.save(secure_filename(f.filename))
        return 'file uploaded succefully'



@app.route('/user/upload/data')
def upload_data():
    app.config['UPLOAD_FOLDER']='./data/'
    return redirect(url_for('upload_file'))


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
@app.route('/user/command/start/<int:id>')
def start_id(id):
    if id in task_index:
        ind=task_index.index(id)
        return "task started successfully:"+task_list[ind].show_info()
    else:
        return "task id not found."

@app.route('/user/command/stop/<int:id>')
def stop_id(id):
    if id in task_index:
        ind=task_index.index(id)
        return "task stoped successfully:"+task_list[ind].show_info()
    else:
        return "task id not found."
    

#查看集群任务进度
@app.route('/user/ask/cluster_info')
def all_cluster():
    pass

@app.route('/user/ask/task')
def all_tasks():
    pass

@app.route('/user/ask/running_task')
def running_task():
    res=''
    for i in task_list:
        if i.statu=='running':
            res+=i.show_info()
    if res=='':
        return "no running task found."
    else:
        return res
    

@app.route('/user/ask/log/<int:task_id>')
def task_log(task_id):
    if task_id in task_index:
        tmp=task_index.index(task_id)
        t=task_list[tmp]
        return t.show_log()
    else:
        return "task id not found."


if __name__=="__main__":
    #app.run(host, port, debug, options)
    app.config['UPLOAD_FOLDER']='./data'
    app.run(debug=True)