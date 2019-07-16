import numpy as np
import json
from functools import partial
import caffe
import time
import sys,os
from pai_pyhdfs import *
import ncs
from easydict import EasyDict as edict
from func_lib import message

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

def get_all(n):
    '''
    This function will get all the result in "fitX.npy",and stack them in a array.
    The result file will be deleted after read.
    In this program there will be exactly 3 result files.

    :return: [array_of_solutions,array_of_fits]
    '''

    def wait_hdfs_files(filepath,hdfs_path="10.20.37.175",port=9000):
        flag=True
        hdfs_client=pyhdfs.HdfsClient(hdfs_path,port)
        count=n
        res=[]
        X=[]

        while count!=0:
            files=hdfs_client.listdir(filepath)
            for k in files:
                #print('in the for loop.')
                if k.startswith('fit'):
                  tmp_files=hdfs_client.listdir(filepath)
                  while k in tmp_files:
                    try:
                      tmp=hdfs_load('/shared/work/',k,delete=False)
                      #time.sleep(1)
                      hdfs_client.delete('/shared/work/'+k)
                      tmp_files=hdfs_client.listdir(filepath)
                    except:
                      tmp_files=hdfs_client.listdir(filepath)

                  tmp_x=tmp[0]
                  tmp_fit=tmp[1]
                  res.append(tmp_fit)
                  X.append(tmp_x)
                  count-=1
        print("all the results recevied!")
        return np.array([X,res])
   
    return wait_hdfs_files('/shared/work/')

def set_solutions(solutions):
    '''
    This function used to split solutions into 3 files, and save them into work path as a .npy file.

    :param solutions:
    :return:
    '''
    print("solutions",solutions,"len:",len(solutions))
    count=0
    for solution in solutions:
      fn='solution_'+str(np.random.randint(0,9999999))+'.npy'
      np.save(fn,solution)
      try:
        hdfs_set_file('./','/shared/work/',fn)
      except:
        pass
      try:
        os.remove(fn)
      except:
        pass
      count+=1
    print('All the solutions have been setted!')

def single_evaluate(content,solver=solver,ob=None):
    the_input,x,batchcount,acc=content
    acc_constrain=paras['acc_constrain']
    x_fit = 1.1

    fi='tmp_model.caffemodel'

    ob.show_debug("model getted,prepare for calculating.")
    solver.net.copy_from(fi)
    ob.show_debug("solver net has loaded.")

    thenet=solver.net
    thenet.blobs['data'].data[:] = the_input
    apply_prune(thenet,x)

    acc = test_net(thenet,  _count=batchcount)

    if acc >= acc - acc_constrain:
      x_fit = get_sparsity(thenet)

    ob.show_debug("evaluating completed!")
    return x_fit

def outer_loop(*,solver=solver,itr=1001,paras=paras):
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

def NCSloop(*content,ob=None):
    '''
    This loop will get the parameters in LoopTest1, and use them to start a ncs loop.
    The result will contained in a file named 'crates_list.npy' in work path.
    The LoopTest1.py will use this file to apply prune the solver net.
    :param tmp_crates:
    :param tmp_ind:
    :param accuracy_: in accuracy.npy file
    :return: create crates_list.npy
    '''

    tmp_crates,tmp_ind,accuracy_=content
    the_input_batch=hdfs_load('/shared/work/','data.npy')
    es = {}

    layer_name=paras['layer_name']
    crates=paras['crates']
    crates_list=paras['crates_list']
    layer_inds=paras['layer_inds']
    es_method=paras['es_method']
    ncs_stepsize=paras['ncs_stepsize']
    
    if es_method == 'ncs':
        __C = edict()
        __C.parameters = {'reset_xl_to_pop':False,
                            'init_value':tmp_crates, 
                            'stepsize':ncs_stepsize, 
                            'bounds':[0.0, 10.], 
                            'ftarget':0, 
                            'tmax':1600, 
                            'popsize':10, 
                            'best_k':1}
        es = ncs.NCS(__C.parameters)
        print('***************NCS initialization***************')
        tmp_x_ = np.array(crates_list)
        tmp_input_x = tmp_crates
        for _ii in range(len(tmp_ind)):
            tmp_x_[layer_inds[tmp_ind[_ii]]] = tmp_input_x[_ii]

        set_solutions([tmp_x_])
        _,tmp_fit = get_all(len([tmp_x_]))
        print('all fitness gotten.')

        es.set_initFitness(es.popsize*tmp_fit)
        print('fit:{}'.format(tmp_fit))
        print('***************NCS initialization***************')

    count=0
    while not es.stop():
        print("now in the es loop.")
        count+=1
        if count==15:
            break
        x = es.ask()
        X = []
        for x_ in x:
            tmp_x_ = np.array(crates_list)
            for _ii in range(len(tmp_ind)):
                tmp_x_[layer_inds[tmp_ind[_ii]]] = x_[_ii]
            X.append(tmp_x_)
        set_solutions(X)
        X_arrange,fit=get_all(len(X))
        X = []
        for x_ in X_arrange:
            tmp_x_ = np.array(len(tmp_ind)*[0.])
            for _ii in range(len(tmp_ind)):
                tmp_x_[_ii]= x_[layer_inds[tmp_ind[_ii]]] 
            X.append(tmp_x_)
        es.tell(X, fit)
        for _ii in range(len(tmp_ind)):
            crates_list[layer_inds[tmp_ind[_ii]]] = es.result()[0][_ii]
    for c_i in range(len(crates_list)):
        crates[layer_name[c_i]] = crates_list[c_i]
    #es_cache[itr]={'compression':-es.result()[1], 'crates':crates_list[:]}
    _tmp_c = np.array(len(crates_list)*[-1.])
    for t_name in tmp_ind:
        _tmp_c[layer_inds[t_name]] = crates[t_name]

    #output
    np.save('crates_list.npy',crates_list)
    hdfs_set_file('./','/shared/work/','crates_list.npy')
    os.remove('crates_list.npy')

def init(content,ob=None,paras=paras):
    '''
    statu:0
    content:one_iter_num,generally,it's a int.
    '''
    msg=message(1,0)
    ob.send_list.put(msg.msg_encode())
    ob.show_debug('init over,wait for respons.')

def main_program(content,ob=None,paras=paras):
    '''
    statu:1
    content:iterated_times
    '''
    max_iter=paras['niter']
    if content<max_iter:
        msg=message(2,content+1001)
        ob.send_list.put(msg.msg_encode())
        ob.show_debug("message is ready to send to loop.")
    else:
        msg=message(499,'Completed! Waiting for the final result...')
        ob.send_list.put(msg.msg_encode())

#--------------Outer Loop--------------------#
proto='./models/lenet300100/lenet_train_test.prototxt'
weights='./models/lenet300100/lenet300100_iter_10000.caffemodel'
solver_path='./models/lenet300100/lenet_solver.prototxt'
es_method='ncs'
origin_proto_name = './models/lenet300100/lenet_origin.prototxt'
parallel_file_name = 'tmp_model.caffemodel'

# cpu/gpu
caffe.set_mode_gpu()
caffe.set_device(0)

# init solver
solver = caffe.SGDSolver(solver_path)

acc_constrain=0.08
niter = 30001
prune_stop_iter = 15000
layer_name = ['ip1','ip2','ip3']
layer_inds = {'ip1':0, 'ip2':1, 'ip3':2}
crates = {'ip1':0.001, 'ip2':0.001, 'ip3':0.001}
crates_list = [0.001, 0.001, 0.001]
gamma = {'ip1':0.0002, 'ip2':0.0002, 'ip3':0.0002}
gamma_star = 0.0002
ncs_stepsize = 50
seed= np.random.randint(1000000) 
np.random.seed([seed])
es_cache = {}
r_count=0


def start_loop(content,ob=None,solver=solver):
    '''
    statu:2
    content: iternum.
    '''
    if content==0:
        solver.step(1)
    
    for itr in range(1,1001):
        tmp_crates=[]
        tmp_ind=[]
        for ii in layer_name:
            tmp_tag=np.power(1+gamma[ii]*itr,-1) > np.random.rand()
            if tmp_tag:
                tmp_ind.append(ii)
                tmp_crates.append(tmp_tag*crates[ii])
        if itr<2000 and itr%10000==1:
            ncs_stepsize/=10.
        if itr%500==0:
            print("Compression:{},Accuracy:{}".format(1./get_sparsity(solver.net),test_net(solver.net,_count=1,_start='ip1')))
        if len(tmp_ind)>0 and itr<prune_stop_iter:
            _tmp_c=np.array(len(crates_list)*[-1.])
            for t_name in tmp_ind:
                _tmp_c[layer_inds[t_name]]=crates[t_name]
            apply_prune(solver.net,_tmp_c)
        if itr%1000==0 and len(tmp_ind)>1 and itr<prune_stop_iter:
            st1=str(tmp_crates)
            st2=str(tmp_ind)
            solver.net.save(parallel_file_name)
            data=solver.net.blobs['data'].data
            # here....
    pass

def get_result(content,ob=None,paras=paras):
    '''
    statu:10
    content:result array
    '''
    print("The final result is:\n",content)
    msg=message(499,"result gotton.")
    ob.send_list.put(msg.msg_encode())


    
    



#for service program get all the functions defined in this module.
def get_funcs():
    dct=dict()
    dct[0]=init
    dct[1]=main_program
    dct[10]=get_result
        