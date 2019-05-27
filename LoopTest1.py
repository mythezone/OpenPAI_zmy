# coding=utf-8
import os
import sys
import caffe
import numpy as np
import ncs
import time
import pdb
from pai_pyhdfs import *

#---------------------------functions--------------------------#
def test_net(thenet, _start='mnist', _count=1):
   '''
    thenet: the object of network
    _start: the layer to start from
    _count: the number of batches to run
   '''
   scores = 0
   for i in range(_count):
      thenet.forward(start=_start)
      scores += thenet.blobs['accuracy'].data
   return scores/_count

def apply_prune(thenet, _crates):
   '''
      thenet: the model to be pruned
      _crates: the list of crates for layers
   '''
   for _id in range(len(layer_name)):
         if _crates[_id] < 0:
           continue
         layer_id = layer_name[_id]
         mask0 = thenet.params[layer_id][2].data.ravel()[0]
         if mask0 == 0:
           thenet.params[layer_id][2].data.ravel()[0] = -_crates[_id]
         else:
           thenet.params[layer_id][2].data.ravel()[0] = 1+_crates[_id]
         # else:
         #   pdb.set_trace()

def get_sparsity(thenet):
   '''
     thenet: the network for checking
   '''
   remain = 0
   total = 0
   for layer_id in layer_name:
      remain += len(np.where(thenet.params[layer_id][2].data != 0)[0])
      remain += len(np.where(thenet.params[layer_id][3].data != 0)[0])
      total += thenet.params[layer_id][0].data.size
      total += thenet.params[layer_id][1].data.size
   #return total*1./(100.*remain)
   return remain*1./total

   
def outer_loop(itr=1001):
    global ncs_stepsize
    global work_path
    global crates_list
    for itr in range(1,itr):
      
      #r = np.random.rand()
      #if itr%500==0 and solver.test_nets[0].blobs['accuracy'].data >= 0.9909:
      #  retrieval_tag.append(itr)
      tmp_crates=[]
      tmp_ind = []
      for ii in layer_name:
          #tmp_crates.append(crates[ii]*(np.power(1+gamma[ii]*itr, -1)>np.random.rand()))
          tmp_tag = np.power(1+gamma[ii]*itr, -1)>np.random.rand()
          if tmp_tag:
            tmp_ind.append(ii)
            tmp_crates.append(tmp_tag*crates[ii])
      if itr < 2000 and itr%10000 == 1:
          ncs_stepsize = ncs_stepsize/10.
      if itr%500 == 0:
          print("Compression:{}, Accuracy:{}".format(1./get_sparsity(solver.net), test_net(solver.net, _count=1, _start="ip1")))
      if len(tmp_ind)>0 and itr < prune_stop_iter:# run at window @6
          _tmp_c = np.array(len(crates_list)*[-1.])
          for t_name in tmp_ind:
              _tmp_c[layer_inds[t_name]] = crates[t_name]
          apply_prune(solver.net, _tmp_c)
      #if len(tmp_ind)>1 and itr < prune_stop_iter:
      if itr%1000==0 and len(tmp_ind)>1 and itr < prune_stop_iter:# run at window @3
          st1=str(tmp_crates)
          st2=str(tmp_ind)
          
          #solver.net.save(work_path+'/tmp.caffemodel')
          solver.net.save(parallel_file_name)
          hdfs_set_file('./','/shared/work/',parallel_file_name)
          data=solver.net.blobs['data'].data
          #print("max",np.max(data))
          hdfs_save('/shared/work/','data.npy',data)
          #np.save(work_path+'/data.npy',data)
          
          accuracy_ = test_net(solver.net, _count=1, _start="ip1")
          #print("accuracy_:",accuracy_)
          # st3=str(accuracy_)
          hdfs_save('/shared/work/','accuracy.npy',accuracy_,delete=False)
          #np.save(work_path+'/accuracy.npy',accuracy_) #save accuracy in a file.
          msg='['+st1+','+st2+']' # message to send to LoopTest2.py.
          with open('ncs_start.txt','w') as f:
                f.write(msg)

          hdfs_set_file('./','/shared/work/','ncs_start.txt',delete=True)

          while True:
            #print("Waiting for NCSloop over")
            '''
            waiting for NCSloop over.
            when the 'ncs_over.txt' file is in the work path, this loop will get the result in crates_list.npy,
            and retraining the model with the solution applied by the ncsloop.
            '''

            f=wait_hdfs_file('/shared/work/','ncs_over.txt',delete=True)
            crate_list=hdfs_load('/shared/work/','crates_list.npy',delete=True)
            apply_prune(solver.net,crate_list)
            solver.step(1)
            return
            
            # time.sleep(10)
            # files=os.listdir(work_path)
            # if files == []:
            #     #print("waitingfor ncsloop over!")
            #     time.sleep(10)
            #     continue
            # else:
            #     for k in files:
            #       if k!='ncs_over.txt':
            #         #print("checking the File name.")
            #         continue
            #       else:
            #         filepath=work_path+"/"+k
            #         print("Get the result of NCSloop")
            #         os.remove(filepath)
            #         crates_list=np.load(work_path+'/crates_list.npy')
            #         apply_prune(solver.net,crates_list)
            #         #retrainning
            #         solver.step(1)
            #         return
            #     time.sleep(10)
            # crates_list=np.load(work_path+'/crates_list.npy')
            # apply_prune(solver.net,crates_list)
      #retrainning
      solver.step(1)
#---------------------------------functions end-----------------------------------#




#----------------------------init------------------------------------#
# model files
proto='./models/lenet300100/lenet_train_test.prototxt'
# based on the network used in DS paper, 97.72 accuracy
#weights='/home/gitProject/Dynamic-Network-Surgery/models/lenet300100/caffe_lenet300100_original.caffemodel'
# based on the network used in IPR, 97.73 accuracy
weights='./models/lenet300100/lenet300100_iter_10000.caffemodel'
solver_path='./models/lenet300100/lenet_solver.prototxt'
es_method='ncs'
origin_proto_name = './models/lenet300100/lenet_origin.prototxt'
parallel_file_name = './tmp_model.caffemodel'
# cpu/gpu
caffe.set_mode_gpu()
caffe.set_device(0)
# init solver
solver = caffe.SGDSolver(solver_path)
# basic parameters
#   accuracy constraint for pruning
acc_constrain=0.08
#   stop iteration count
#niter = 20501
niter = 30001
#   stop pruning iteration count
prune_stop_iter = 15000
#   the list of layer names
layer_name = ['ip1','ip2','ip3']
#   the dict of layer names to its arrary indices
layer_inds = {'ip1':0, 'ip2':1, 'ip3':2}
#   the dict of crates for each layer
crates = {'ip1':0.001, 'ip2':0.001, 'ip3':0.001}
#   the list of the crates
crates_list = [0.001, 0.001, 0.001]
#   the gamma for each layer
gamma = {'ip1':0.0002, 'ip2':0.0002, 'ip3':0.0002}
gamma_star = 0.0002
ncs_stepsize = 50
#   random see for numpy.random
#seed= 981118 # for 112x compression  with acc_constrain=0.3
#seed=961449 # for 113.5x compression with acc_constrain=0.08
seed= np.random.randint(1000000) 
np.random.seed([seed])
#   the dict to store intermedia results
es_cache = {}
#retrieval_tag=[]
r_count=0

work_path="./work"
#---------------------------init end---------------------------#


#--------------------------start of loop1----------------------#
print("OuterLoop is runing!")

solver.step(1)
flag=True

while flag:
    '''
    waiting for "new_iter.txt" to start a new loop.
    when the loop is over, "report.txt" will be created in the work path.
    '''

    f=wait_hdfs_file("/shared/work/",'new_itr.txt',delete=True)
    with open(f,'r') as ff:
      msg=ff.read()
      if msg=='over':
        flag=False
        continue
      else:
        itr=eval(msg)
        print('receive the number of itr:',itr)
    
    os.remove(f)

    with open('report.txt','w') as ff:
      ff.write('15002')

    outer_loop(1001)
    hdfs_set_file('./','/shared/work/','report.txt',delete=False)
