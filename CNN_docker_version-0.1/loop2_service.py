# coding=utf-8
import os
import sys
import numpy as np
from lcg_random import lcg_rand
import ncs
from easydict import EasyDict as edict
import time
import pdb
from pai_pyhdfs import *
from base  import *

#-----------------------init---------------------------#
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
acc_constrain=0.08
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
work_path="/shared/work/"

#-----------------------init over-----------------------#

# definition of many axuliliary methods
#   run the network on its dataset
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

#   Set the crates of each layer, the pruning will happen in the next forward action
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
        # elif mask0 == 1:
         else:
           thenet.params[layer_id][2].data.ravel()[0] = 1+_crates[_id]
        #  else:
        #    pdb.set_trace()

#  calcuate the sparsity of a network model
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

# def get_all(n):
#     '''
#     This function will get all the result in "fitX.npy",and stack them in a array.
#     The result file will be deleted after read.
#     In this program there will be exactly 3 result files.

#     :return: [array_of_solutions,array_of_fits]
#     '''
    # count=0
    # res=[]
    # X=[]
    # while count<n:
    #     files=os.listdir('./work/')
    #     for k in files:
    #         if k.startswith('fit'):
    # def wait_hdfs_files(filepath,hdfs_path="10.20.37.175",port=9000):

    #     count=n
    #     res=[]
    #     X=[]

    #     while count!=0:
    #         files=hdfs_client.listdir(filepath)
    #         for k in files:
    #             #print('in the for loop.')
    #             if k.startswith('fit'):
    #               tmp_files=hdfs_client.listdir(filepath)
    #               while k in tmp_files:
    #                 try:
    #                   tmp=hdfs_load('/shared/work/',k,delete=False)
    #                   #time.sleep(1)
    #                   hdfs_client.delete('/shared/work/'+k)
    #                   tmp_files=hdfs_client.listdir(filepath)
    #                 except:
    #                   tmp_files=hdfs_client.listdir(filepath)

    #               tmp_x=tmp[0]
    #               tmp_fit=tmp[1]
    #               res.append(tmp_fit)
    #               X.append(tmp_x)
    #               count-=1
    #     print("all the results recevied!")
    #     return np.array([X,res])
   
    # return wait_hdfs_files('/shared/work/')
                            
class loop2_worker(Process):
    def __init__(self,recv_list,send_list,max=10,debug=True):
        super().__init__()
        self.recv_list=recv_list
        self.send_list=send_list
        self.accuracy=0
        self.debug=debug
        self.max=max
        self.res=list()
        self.X=list()
        self.count=0

    
    def log(self,msg):
        if self.debug==False:
            return 
        else:
            print(msg)
    
    def run(self):
        print("loop2 service is running...")
        while True:
            if self.recv_list.empty():
                time.sleep(1)
                continue
            else:
                msg=self.recv_list.get()
                statu,content=json.loads(msg.decode())
                if statu==41:
                    self.accuracy=content

                elif statu==42:
                    tmp_crates=content[0]
                    tmp_ind=content[1]
                    # NCSloop(tmp_crates,tmp_ind,self.accuracy)

                    self.log('ncs loop is complete.')
                    #@print("NCS loop is completed.")
                    new_msg=message(3,'complete').msg_encode()
                    self.send_list.put(new_msg)
                
                elif statu==43:
                    self.count+=1
                    tmp_x=content[0]
                    tmp_fit=content[1]
                    self.res.append(tmp_fit)
                    self.X.append(tmp_x)
                    if self.count==self.max:
                        self.result=np.array([self.X,self.res])
                        self.count=0
                        self.res=list()
                        self.X=list()





    


def set_solutions(solutions,send_list):
    '''
    This function used to split solutions into 3 files, and save them into work path as a .npy file.

    :param solutions:
    :return:
    '''
    print("solutions",solutions,"len:",len(solutions))
    count=0
    for solution in solutions:
      msg=message(51,solution).msg_encode()
      send_list.put(msg)
      count+=1
    print('All the solutions have been setted!')

def NCSloop(tmp_crates,tmp_ind,accuracy_):
    '''
    This loop will get the parameters in LoopTest1, and use them to start a ncs loop.
    The result will contained in a file named 'crates_list.npy' in work path.
    The LoopTest1.py will use this file to apply prune the solver net.
    :param tmp_crates:
    :param tmp_ind:
    :param accuracy_: in accuracy.npy file
    :return: create crates_list.npy
    '''
    f = wait_file('./work/','data.npy')
    the_input_batch= np.load(f)
    # the_input_batch=hdfs_load('/shared/work/','data.npy')
    es = {}
    
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

        set_solutions([tmp_x_],send_list)
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
    np.save('crates_list.npy',crates_list)
    hdfs_set_file('./','/shared/work/','crates_list.npy')
    os.remove('crates_list.npy')



time.sleep(3)
##--start loop:
while True:
    '''
    waiting for "ncs_start.txt" file to start work.
    when one loop is over,create a "fitness_over.txt" file in work path.
    '''
    f=wait_hdfs_file('/shared/work/','ncs_start.txt',delete=True)
    with open(f,'r') as ff:
      msg=ff.read()
      if msg=='exit':
        continue
      else:
        msg=eval(msg)
        tmp_crates=msg[0]
        tmp_ind=msg[1]
    
    tmp_accuracy_=hdfs_load('/shared/work/','accuracy.npy')
    print('accuracy is loaded.')
    NCSloop(tmp_crates,tmp_ind,tmp_accuracy_)
    print("NCSloop is completed!")
    os.remove(f)
    with open('ncs_over.txt','w') as ff:
      ff.write('complete!')
    hdfs_set_file('./','/shared/work/','ncs_over.txt')