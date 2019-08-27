import numpy as np
import json
from functools import partial
import caffe
import time
import sys,os
sys.path.insert(0, './python/')
import ncs
from base import *
from easydict import EasyDict as edict
import pdb
from base import *

config=read_json("config.json")

proto=config['proto']

weights='./models/lenet300100/lenet300100_iter_10000.caffemodel'
solver_path='./models/lenet300100/lenet_solver.prototxt'
origin_proto_name = './models/lenet300100/lenet_origin.prototxt'
parallel_file_name = './tmp_model.caffemodel'

es_method=config['es_method']
acc_constrain=config['acc_constrain']
niter=config['niter']
prune_stop_iter=config['prune_stop_iter']
layer_name=config['layer_name']
layer_inds=config['layer_inds']
crates=config['crates']
crates_list=config['crates_list']
gamma=config['gamma']
gamma_star=config['gamma_star']
ncs_stepsize=config['ncs_stepsize']
seed=config['seed']
np.random.seed([seed])
es_cache=config['es_cache']
r_count=config['r_count']


# caffe.set_mode_gpu()
# caffe.set_device(0)
# solver=caffe.SGDSolver(solver_path)



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
         elif mask0 == 1:
           thenet.params[layer_id][2].data.ravel()[0] = 1+_crates[_id]
         else:
           pdb.set_trace()

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

#  evaluate the accuracy of a network with a set of crates respect to a original accuracy
def evaluate(thenet, x_set, batchcount=1, accuracy_ontrain=0.9988):
   fitness=[]
   X=[]
   for x in x_set:
     x_fit = 1.1
     apply_prune(thenet,x)
     acc = test_net(thenet, _start='ip1', _count=batchcount)
     if acc >= accuracy_ontrain - acc_constrain:
       x_fit = get_sparsity(thenet)
     fitness.append(x_fit)
     X.append(x)
   return (X, fitness)

def single_evaluate(thenet,the_input_batch,x,batchount,acc):
    #print("Start calcualting:")
    x_fit=1.1
    thenet.blobs['data'].data[:]=the_input_batch
    apply_prune(thenet,x)
    acc=test_net(thenet,_count=batchount)
    if acc>=acc-acc_constrain:
        x_fit=get_sparsity(thenet)
    #print("evaluating completed!!")
    return x_fit

class worker(Process):
    def __init__(self,recv_list,send_list):
        Process.__init__(self)
        self.recv_list=recv_list
        self.send_list=send_list
        self.the_input_batch=None
        

    def run(self):
        print("Worker is running:")
        caffe.set_mode_gpu()
        caffe.set_device(0)
        # init solver
        solver = caffe.SGDSolver(solver_path)
        self.thenet=solver.net
        while True:

            if self.recv_list.empty():
                time.sleep(2)
                continue
            else:
                msg=self.recv_list.get()
                print("Get a message:",msg.decode())
                new_msg=message.b2m(msg)
                statu,content=new_msg.statu,new_msg.content
                if statu in [1,100]:
                    print("start the work:")
                    #whole_function()
                    continue
                elif statu==31:
                    self.tmp_accuracy_=content
                    print("accuracy is recvd: ",content)
                    continue
                elif statu==32:
                    print("data file recvd!")
                    time.sleep(1)
                    self.the_input_batch=np.load('data.npy')
                    print("data loaded.")
                    continue
                elif statu==33:
                    solver.net.copy_from('./tmp_model.caffemodel')
                    self.thenet=solver.net
                    
                    print("net file recvd!!!!!!!!!!!!!!!")
                    continue
                elif statu==41:
                    ff=content
                    fit=single_evaluate(self.thenet,self.the_input_batch,ff,1,self.tmp_accuracy_)
                    new_msg=message(51,[ff,fit]).msg_encode()
                    self.send_list.put(new_msg)
                    #print("one fit is ready.")
                    continue
                elif statu==102:
                    _,file_name,_file_path=content
                    if file_name=='data.npy':
                        print('data recvd.')
                        self.the_input_batch=np.load('data.npy')
                    elif file_name==parallel_file_name:
                        solver.net.copy_from('./tmp_model.caffemodel.npy')
                        self.thenet=solver.net
                        print('net recvd')
                    print("file revd success in msg list.")
                    continue
                else:
                    print("wrong statu:",statu)



if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()
    # wait_list=multiprocessing.Queue()
    
    ser=server(recv_list,send_list,name='evaluator',port=50005)
    wkr=worker(recv_list,send_list)
    mgr=messager(recv_list,send_list,name='evaluator')

    ser.start()
    wkr.start()
    mgr.start()
    print("main process over")

