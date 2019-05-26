# coding=utf-8
import os
os.environ['GLOG_minloglevel'] = '2'
import sys
sys.path.insert(0, './python/')
import caffe
import numpy as np
from lcg_random import lcg_rand
import ncs
from easydict import EasyDict as edict
import time
import pdb
from pyspark.context import SparkContext
sc=SparkContext()


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
caffe.set_device(1)
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
# load the pretrained caffe model
work_path="./work"

if weights:
  solver.net.copy_from(weights)

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
         #elif mask0 == 1:
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

#  evaluate the accuracy of a network with a set of crates respect to a original accuracy
#  thenet is the broadcasted reference model
def evaluate(the_input, x_set, batchcount=1, accuracy_ontrain=0.9988):
   fitness=[]
   X=[]
   if len(x_set)==0:
     return [[],[]]
   # distributed evaluation by spark
   def single_eval(x):
     import sys
     sys.path.insert(0, './python/')
     import os
     os.environ['GLOG_minloglevel'] = '2'
     import caffe
     x_fit = 1.1
     thenet = caffe.Net(origin_proto_name, caffe.TEST)
     thenet.copy_from(parallel_file_name)
     #print("shape of thenet, the_input", thenet.blobs['data'].data.shape, the_input.value.shape)
     thenet.blobs['data'].data[:] = the_input
     #print("difference:", (thenet.blobs['data'].data - the_input.value).mean())
     apply_prune(thenet,x)
     #acc = test_net(thenet, _start='ip1', _count=batchcount)
     acc = test_net(thenet,  _count=batchcount)
     #print(the_input.value.shape)
     #acc = thenet.forward(data=the_input.value).blobs['accuracy'].data
     #print('acc:',acc,'on-con',accuracy_ontrain - acc_constrain)
     if acc >= accuracy_ontrain - acc_constrain:
       x_fit = get_sparsity(thenet)
     #print('accuracy_ontrain, acc',accuracy_ontrain, acc)
     return ([x], [x_fit])

   def merge_results(a, b):
     return (a[0]+b[0], a[1]+b[1])

   final_results = sc.parallelize(x_set).map(single_eval).reduce(merge_results)
   #print('individual num:', len(x_set))
   #print(final_results)
   return final_results


time.sleep(5)
#the_input_batch = sc.broadcast(solver.net.blobs['data'].data)
the_input_batch = np.load('work/data.npy')

while True:
    '''
        this loop will wait for the solution file, and return [arrary of solutions,array of fitnesses] in a file.
        '''
    files=os.listdir(work_path)
    if files == []:
        print("Evaluation Program is sleeping!")
        time.sleep(10)
        continue
    else:
        for k in files:
          if k not in ['solutions2.npy','fitness_over.txt']:
            #if np.random.rand()>0.8:
              #print("checking the File name.")
            continue
          else:
            if k=='solutions2.npy':
              #print("solutions gotten,Calculating the fitnesses.")
              filepath=work_path+"/"+k
              X=np.load(filepath)
              accuracy=np.load(work_path+'/accuracy.npy')
              #print(X)
              if len(X)==0:
                np.save(work_path+'/fit2.npy',[[],[]])
                os.remove(filepath)
                break
              fit=evaluate(the_input_batch,X,1,accuracy)
              os.remove(filepath)
              filepath=work_path+'/fit2.npy'
              np.save(filepath,np.array(fit))
              break
            else:
              exit()
        time.sleep(5)