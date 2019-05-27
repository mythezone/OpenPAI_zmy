import pyhdfs
import time
import numpy as np
import os,sys

def wait_hdfs_file(filepath,filename,delete=False,hdfs_path="10.20.37.175",port=9000):
    flag=True
    hdfs_client=pyhdfs.HdfsClient(hdfs_path,port)
    while flag:
        files=hdfs_client.listdir(filepath)
        if files == []:
            time.sleep(1)
            continue
        else:
            if filename in files:
                file_path=filepath+filename
                f=hdfs_get_file(filepath,filename,"./",delete)
                flag=False
            else:
                time.sleep(1)
    print('The waited file has been retrived to local machine!')
    return f

def hdfs_set_file(local_file_path,remote_file_path,filename,hdfs_path="10.20.37.175",port=9000):
    hdfs_client=pyhdfs.HdfsClient(hdfs_path,port)
    files=hdfs_client.listdir(remote_file_path)
    if filename in files:
        try:
            hdfs_client.delete(remote_file_path+filename)
        except:
            pass
    hdfs_client.copy_from_local(local_file_path+filename,remote_file_path+filename)
    print("set Completed!")

def hdfs_get_file(remote_path,filename,local_path,delete=False,hdfs_path='10.20.37.175',port=9000):
    hdfs_client=pyhdfs.HdfsClient(hdfs_path,port)
    try:
        hdfs_client.copy_to_local(remote_path+filename,local_path+filename)
    except:
        time.sleep(2)
        hdfs_client.copy_to_local(remote_path+filename,local_path+filename)
    print("load completed!")
    if delete:
        try:
            hdfs_client.delete(remote_path+filename)
        except:
            pass
    return local_path+filename

def hdfs_load(remote_path,filename,local_path='./',delete=False):
    f=hdfs_get_file(remote_path,filename,local_path,delete)
    d=np.load(f)
    try:
        os.remove(local_path+filename)
    except:
        pass
    return d

def hdfs_save(remote_path,filename,arr,local_path='./',delete=False):
    np.save(local_path+filename,arr)
    hdfs_set_file(local_path,remote_path,filename)

def hdfs_init_fold(remote_path,hdfs_path="10.20.37.175",port=9000):
    hdfs_client=pyhdfs.HdfsClient(hdfs_path,port)
    try:
      files=hdfs_client.listdir(remote_path)
    except:
      hdfs_client.mkdirs(remote_path)
      return
    if files==[]:
      return
    else:
      for k in files:
        try:
            hdfs_client.delete(remote_path+k)
        except:
            pass
      return

def set_work(itr=0,tmax=30001,remote_path='/shared/work/'):
    '''
    set the "new_iter.txt" file.
    :param itr: the number of iter
    :return: nothing but will set "new_iter.txt" in work_path containing itr or "over".
    '''
    if itr>tmax:
      msg="over"
    else:
      msg="1001"
    with open("new_itr.txt",'w') as f:
      f.write(msg)
    hdfs_set_file('./',remote_path,"new_itr.txt")

