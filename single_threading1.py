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
#from pyspark.context import SparkContext
#sc=SparkContext()


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
        time.sleep(1)
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
# load the pretrained caffe model
work_path="/shared/work/"

# if weights:
#   solver.net.copy_from(weights)

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

def single_evaluate(the_input,x,batchcount,acc):
    print("In the single_evaluation function!Version: 2.0")
    print("x",x)
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



#the_input_batch = sc.broadcast(solver.net.blobs['data'].data)
time.sleep(5)
the_input_batch= hdfs_load('/shared/work/','data.npy')
#the_input_batch = np.load('work/data.npy')
hdfs_client=pyhdfs.HdfsClient('10.20.37.175',9000)
while True:
    '''
    this loop will wait for the solution file, and return [arrary of solutions,array of fitnesses] in a file.
    '''
    files=hdfs_client.listdir('/shared/work/')
    for f in files:
      if f.startswith('solution'):
        accuracy=hdfs_load('/shared/work/','accuracy.npy')
        print("get a solution,calculating...version:2")
        ff=hdfs_load('/shared/work/',f,delete=True)
        print("ff",ff)
        #hdfs_client.delete('/shared/work/'+f)
        fit=single_evaluate(the_input_batch,ff,1,accuracy)
        #fit=np.random.uniform(0,1)
        fn='fit_'+f
        np.save(fn,np.array([ff,fit]))
        print("npy file has been setted!")
        hdfs_set_file('./','/shared/work/',fn)
        time.sleep(1)
        os.remove(fn)
        hdfs_client.delete('/shared/work/'+f)
        print("OK,fitness has been setted.  waiting for the next evaluation.")
    time.sleep(1)
