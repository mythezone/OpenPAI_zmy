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
parallel_file_name = 'tmp_model.caffemodel'

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

def whole_function(recv_list,send_list,wait_list):
    #  Adaptive dynamic surgery
    global ncs_stepsize
    global crates_list
    caffe.set_mode_gpu()
    caffe.set_device(0)
    solver=caffe.SGDSolver(solver_path)
    start_time = time.time()

    if weights:
        solver.net.copy_from(weights)

    solver.step(1)
    for itr in range(niter):
        tmp_crates=[]
        tmp_ind = []
        for ii in layer_name:
            #tmp_crates.append(crates[ii]*(np.power(1+gamma[ii]*itr, -1)>np.random.rand()))
            tmp_tag = np.power(1+gamma[ii]*itr, -1)>np.random.rand()
            if tmp_tag:
                tmp_ind.append(ii)
                tmp_crates.append(tmp_tag*crates[ii])
        if itr < 2000 and itr%10000 == 0:
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
            # st1=str(tmp_crates)
            # st2=str(tmp_ind)
            # print(st1,st2)
            solver.net.save(parallel_file_name)
            tmp_msg=message(102,[33,parallel_file_name,'./']).msg_encode()
            send_list.put(tmp_msg)

            data=solver.net.blobs['data'].data
            np.save('data.npy',data)
            tmp_msg=message(102,[32,'data.npy','./']).msg_encode()
            send_list.put(tmp_msg)

            accuracy_ = test_net(solver.net, _count=1, _start="ip1")
            tmp_msg=message(31,accuracy_).msg_encode()
            send_list.put(tmp_msg)

            tmp_msg=message(34,[tmp_crates,tmp_ind]).msg_encode()
            send_list.put(tmp_msg)

            crates_list=wait_message(wait_list,35)
            apply_prune(solver.net,crates_list)

        solver.step(1)

    end_time = time.time()
    # record 
    import datetime
    now = datetime.datetime.now()
    time_styled = now.strftime("%Y-%m-%d %H:%M:%S")
    out_ = open('record_{}.txt'.format(time_styled), 'w')
    for key,value in es_cache.items():
        out_.write("Iteration[{}]:\t{}x\t{}\n".format(key,value['compression'],value['crates']))
    out_.close()
    print('random seed:{}'.format(seed))
    print("Time:%.4f" % ((end_time - start_time)/60.))


class worker(Process):
    def __init__(self,recv_list,send_list,wait_list,algo_route=dict()):
        Process.__init__(self)
        self.recv_list=recv_list
        self.send_list=send_list
        self.route=dict()
        self.algo_route=algo_route
        self.wait_list=wait_list

    def run(self):
        print("Worker is running:")
        while True:

            if self.recv_list.empty():
                time.sleep(2)
                continue
            else:
                msg=self.recv_list.get()
                print("Get a message:",msg.decode())
                new_msg=message.b2m(msg)
                statu,_content=new_msg.statu,new_msg.content
                if statu in [1,2,100]:
                    print("start the work on statu:",statu)
                    tmp_p=multiprocessing.Process(target=whole_function,args=(self.recv_list,self.send_list,self.wait_list))
                    tmp_p.start()
                elif statu==35:
                    self.wait_list.put(msg)
                    print("a waited msg has been recvd.")
                else:
                    print("wrong statu:",statu)



if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()
    wait_list=multiprocessing.Queue()
    ser=server(recv_list,send_list,name='loop1',port=50003)
    wkr=worker(recv_list,send_list,wait_list)
    mgr=messager(recv_list,send_list,name='loop1')

    ser.start()
    wkr.start()
    mgr.start()
    print("main process over")

