# coding=utf-8
import os,sys
import numpy as np
import time
from pai_pyhdfs import *
from base import *
from multiprocessing import process
import multiprocessing
import json


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
hdfs_init_fold(work_path)
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