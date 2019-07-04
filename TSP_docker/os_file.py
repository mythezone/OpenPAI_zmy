import os,sys
import numpy as np
import time

def clean_work_path(file_path):
    files=os.listdir(file_path)
    if files==[]:
        return
    for i in files:
        os.remove(file_path+i)
    return 

def wait_msg_file(file_path,file_name,delete=False):
    files=os.listdir(file_path)
    while True:
        if file_name in files:
            with open(file_path+file_name,'r') as ff:
                msg=ff.read()
            if delete==True:
                os.remove(file_path+file_name)
            return msg
        else:
            time.sleep(1)
            files=os.listdir(file_path)

def wait_np_file(file_path,file_name,delete=False):
    files=os.listdir(file_path)
    while True:
        if file_name in files:
            arr=np.load(file_path+file_name)
            if delete==True:
                os.remove(file_path+file_name)
            return arr
        else:
            time.sleep(1)
            files=os.listdir(file_path)

def wait_np_file_start(file_path,file_start,delete=False):
    files=os.listdir(file_path)
    while True:
        for i in files:
            if i.startswith(file_start):
                arr=np.load(file_path+i,allow_pickle=True)
                if delete==True:
                    os.remove(file_path+i)
                return arr
        time.sleep(2)
        files=os.listdir(file_path)

def set_np_file(file_path,file_name,arr):
    arr=np.array(arr)
    try:
        os.mkdir(file_path)
    except:
        pass
    np.save(file_path+file_name,arr)
    return






