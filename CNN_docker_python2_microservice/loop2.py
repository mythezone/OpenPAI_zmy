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

def set_solutions(solutions,send_list):
    #count=0
    for solution in solutions:
        print("solution:",solution)
        msg=message(41,list(solution)).msg_encode()
        send_list.put(msg)
    print("all solutions setted.")

def get_all(n,wait_list):
    count=n
    res=[]
    X=[]
    while True:
        if wait_list.empty():
            #print("wait_list is empty.")
            time.sleep(2)
        else:
            #print("get a result!!")
            msg=wait_list.get()
            new_msg=message.b2m(msg)
            statu,content=new_msg.statu,new_msg.content
            if statu==51:
                tmp_x,tmp_fit=content
                res.append(tmp_fit)
                X.append(tmp_x)
                count-=1
                if count==0:
                    print("all the results recvd!!")
                    return np.array([X,res])
            else:
                print('get a wrong statu msg:',statu)
                wait_list.put(msg)
                
        


def ncs_loop(tmp_crates,tmp_ind,the_input_batch,send_list,wait_list):
    

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
    _,tmp_fit = get_all(len([tmp_x_]),wait_list)
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
        set_solutions(X,send_list)
        X_arrange,fit=get_all(len(X),wait_list)
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

    msg=message(35,crates_list).msg_encode()
    send_list.put(msg)




class worker(Process):
    def __init__(self,recv_list,send_list,wait_list):
        Process.__init__(self)
        self.recv_list=recv_list
        self.send_list=send_list
        self.wait_list=wait_list
        self.the_input_batch=None


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
                statu,content=new_msg.statu,new_msg.content
                if statu in [1,100]:
                    print("start the work:")
                    #whole_function()
                elif statu==31:
                    self.tmp_accuracy_=content
                    print("accuracy is recvd: ",content)
                elif statu==32:
                    print("data file recvd!")
                    self.the_input_batch=np.load('data.npy')
                    print("data loaded.")
                elif statu==33:
                    print("net file recvd!")
                elif statu==34:
                    self.tmp_crates,self.tmp_ind=content
                    print("parameters gotton,Loop2 will running!!!!!",content)
                    tmp_p=multiprocessing.Process(target=ncs_loop,args=(self.tmp_crates,self.tmp_ind,self.the_input_batch,self.send_list,self.wait_list))
                    tmp_p.start()
                elif statu==51:
                    print("a waited msg is coming!")
                    self.wait_list.put(msg)
                    
                elif statu==102:
                    _,file_name,file_path=content
                    if file_name=='data.npy':
                        print('data recvd.')
                        self.the_input_batch=np.load('data.npy')
                    elif file_name==parallel_file_name:
                        print('net recvd')
                        
                    print("file revd success in msg list.")
                else:
                    print("wrong statu:",statu)
                    


if __name__=="__main__":
    recv_list=multiprocessing.Queue()
    send_list=multiprocessing.Queue()
    wait_list=multiprocessing.Queue()
    
    ser=server(recv_list,send_list,name='loop2',port=50004)
    wkr=worker(recv_list,send_list,wait_list)
    mgr=messager(recv_list,send_list,name='loop2')

    ser.start()
    wkr.start()
    mgr.start()


