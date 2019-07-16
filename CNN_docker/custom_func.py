import numpy as np
import json
from functools import partial
import caffe
import time
import sys,os

paras={
    'proto':'./models/lenet300100/lenet_train_test.prototxt',
    'weights':'./models/lenet300100/lenet300100_iter_10000.caffemodel',
    'solver_path':'./models/lenet300100/lenet_solver.prototxt',
    'es_method':'ncs',
    'origin_proto_name':'./models/lenet300100/lenet_origin.prototxt',
    'parallel_file_name':'tmp_model.caffemodel',
    'work_path':"/shared/work/",
    'acc_constrain':0.08,
    'niter':30001,
    'count':0,
    'prune_stop_iter':15000,
    'layer_name':['ip1','ip2','ip3'],
    'layer_inds':{'ip1':0, 'ip2':1, 'ip3':2},
    'crates':{'ip1':0.001, 'ip2':0.001, 'ip3':0.001},
    'crates_list':[0.001, 0.001, 0.001],
    'gamma':{'ip1':0.0002, 'ip2':0.0002, 'ip3':0.0002},
    'gamma_star':0.0002,
    'ncs_stepsize':50,
    'r_count':0,
    'es_cache':{},
    'acc_constrain':0.08

}

caffe.set_mode_gpu()
caffe.set_device(0)
solver = caffe.SGDSolver(paras['sovler_path'])

def test_net(thenet,_start='mnist',_count=1):
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
   layer_name=paras['layer_name']
   for _id in range(len(layer_name)):
         if _crates[_id] < 0:
           continue
         layer_id = layer_name[_id]
         mask0 = thenet.params[layer_id][2].data.ravel()[0]
         if mask0 == 0:
           thenet.params[layer_id][2].data.ravel()[0] = -_crates[_id]
         else:
           thenet.params[layer_id][2].data.ravel()[0] = 1+_crates[_id]

def get_sparsity(thenet):
   '''
     thenet: the network for checking
   '''
   remain = 0
   total = 0
   layer_name=paras['layer_name']
   for layer_id in layer_name:
      remain += len(np.where(thenet.params[layer_id][2].data != 0)[0])
      remain += len(np.where(thenet.params[layer_id][3].data != 0)[0])
      total += thenet.params[layer_id][0].data.size
      total += thenet.params[layer_id][1].data.size
   return remain*1./total

def single_evaluate(the_input,x,batchcount,acc,solver=solver):
    print("In the single_evaluation function!Version: 2.0")
    print("x",x)
    acc_constrain=paras['acc_constrain']
    x_fit = 1.1
    #thenet = caffe.Net(origin_proto_name, caffe.TEST)
    # thenet.copy_from(parallel_file_name)
    #files=os.listdir('./models/lenet300100')
    #print("files",files)
    # s = caffe.SGDSolver(solver_path)
    #print("S loaded.")
    fi=hdfs_get_file('/shared/work/','tmp_model.caffemodel','./')
    print("model getted,prepare for calculating.")
    solver.net.copy_from(fi)
    print("solver net has loaded.")
    thenet=solver.net
    #print("shape of thenet, the_input", thenet.blobs['data'].data.shape, the_input.value.shape)
    thenet.blobs['data'].data[:] = the_input
    #print("difference:", (thenet.blobs['data'].data - the_input.value).mean())
    apply_prune(thenet,x)
    #acc = test_net(thenet, _start='ip1', _count=batchcount)
    acc = test_net(thenet,  _count=batchcount)
    #print(the_input.value.shape)
    #acc = thenet.forward(data=the_input.value).blobs['accuracy'].data
    if acc >= acc - acc_constrain:
      x_fit = get_sparsity(thenet)
    #print('accuracy_ontrain, acc',accuracy_ontrain, acc)
    print("evaluating completed!")
    return x_fit

def outer_loop(solver=solver,itr=1001,paras=paras):
    # global ncs_stepsize
    # global work_path
    # global crates_list

    layer_name=paras['layer_name']
    gamma=paras['gamma']
    crates=paras['crates']
    prune_stop_iter=paras['prune_stop_iter']
    crates_list=paras['crates_list']
    layer_inds=paras['layer_inds']
    parallel_file_name=paras['parallel_file_name']

    for itr in range(1,itr):
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
      if itr%1000==0 and len(tmp_ind)>1 and itr < prune_stop_iter:# run at window @3
          st1=str(tmp_crates)
          st2=str(tmp_ind)
          solver.net.save(parallel_file_name)
          hdfs_set_file('./','/shared/work/',parallel_file_name)
          data=solver.net.blobs['data'].data
          hdfs_save('/shared/work/','data.npy',data)
          accuracy_ = test_net(solver.net, _count=1, _start="ip1")
          #print("accuracy_:",accuracy_)
          # st3=str(accuracy_)
          hdfs_save('/shared/work/','accuracy.npy',accuracy_,delete=False)
          #np.save(work_path+'/accuracy.npy',accuracy_) #save accuracy in a file.
          msg='['+st1+','+st2+']' # message to send to LoopTest2.py.
          with open('ncs_start.txt','w') as f:
                f.write(msg)
          hdfs_set_file('./','/shared/work/','ncs_start.txt')

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
            
      solver.step(1)

class profile:
    def __init__(self):
        self.para=dict(paras) #save the  parameters.
        self.funcs=dict() #save the functions.
        