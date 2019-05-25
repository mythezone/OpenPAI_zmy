# coding=utf-8
import os
#os.environ['GLOG_minloglevel'] = '2'
import sys
#sys.path.insert(0, './python/')
import numpy as np
#from easydict import EasyDict as edict
import time
#import pdb

#------------------------------hdfs functions------------------------------#
import pyhdfs

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
        hdfs_client.delete(remote_file_path+filename)
    hdfs_client.copy_from_local(local_file_path+filename,remote_file_path+filename)
    print("set Completed!")

def hdfs_get_file(remote_path,filename,local_path,delete=False,hdfs_path='10.20.37.175',port=9000):
    hdfs_client=pyhdfs.HdfsClient(hdfs_path,port)
    hdfs_client.copy_to_local(remote_path+filename,local_path+filename)
    print("load completed!")
    if delete:
        hdfs_client.delete(remote_path+filename)
    return local_path+filename

def hdfs_load(remote_path,filename,local_path='./',delete=False):
    f=hdfs_get_file(remote_path,filename,local_path,delete)
    d=np.load(f)
    os.remove(local_path+filename)
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
        hdfs_client.delete(remote_path+k)
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

#----------------------------end of hdfs functions-----------------------------#


'''
This is the init main program.
It will clean the work fold first.
Then a file named new_iter.txt will be created in the work_path, containing a string of the iternum.
Scanning the work_path for a file named "report.txt" containing a string of the iter number.
If the number is larger than niter,the program will exit.
'''

#-----------------------------main--------------------------------#
print("Main.py is runing!")

#-------init-------------#
niter = 30001
work_path='/shared/work/'
#hdfs_init_fold(work_path)
count=0
set_work()
#------end of init-------#


flag=True
while flag:
    '''
    Set "new_iter.txt" to start the outloop.
    Scanning for "report.txt" to decide continue or exit.
    '''
    f=wait_hdfs_file('/shared/work/','report.txt',delete=True)
    with open(f,'r') as ff:
      msg=ff.read()
      #os.remove(f)
      count+=eval(msg)
      set_work(count)
      if count>niter:
        print("Program is over!Waiting for exit!")
        flag=False
    time.sleep(1)    

#--------------------------end of main------------------------------#