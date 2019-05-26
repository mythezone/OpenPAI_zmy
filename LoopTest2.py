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
#import socket


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
caffe.set_mode_cpu()
#caffe.set_device(0)
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

# print("NCSLoop is runing!")
# sc=SparkContext()
# print("sc context has been set.")

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

#  evaluate the accuracy of a network with a set of crates respect to a original accuracy
#  thenet is the broadcasted reference model
def evaluate(the_input, x_set, batchcount=1, accuracy_ontrain=0.9988):
   '''
   the_input:training data
   x_set:the solutions
   accuracy_ontrain: the accuracy.
   return : [array of solutions,array of fitnesses]
   '''
   fitness=[]
   X=[]
   # distributed evaluation by spark
   def single_eval(x):
     import sys
     sys.path.insert(0, './python/')
     import os
     os.environ['GLOG_minloglevel'] = '2'
     import caffe
     x_fit = 1.1
     #thenet = caffe.Net(origin_proto_name, caffe.TEST)
     # thenet.copy_from(parallel_file_name)
     s = caffe.SGDSolver(solver_path)
     s.net.copy_from(parallel_file_name)
     thenet=s.net
     #print("shape of thenet, the_input", thenet.blobs['data'].data.shape, the_input.value.shape)
     thenet.blobs['data'].data[:] = the_input
     #print("difference:", (thenet.blobs['data'].data - the_input.value).mean())
     apply_prune(thenet,x)
     #acc = test_net(thenet, _start='ip1', _count=batchcount)
     acc = test_net(thenet,  _count=batchcount)
     #print(the_input.value.shape)
     #acc = thenet.forward(data=the_input.value).blobs['accuracy'].data
     if acc >= accuracy_ontrain - acc_constrain:
       x_fit = get_sparsity(thenet)
     #print('accuracy_ontrain, acc',accuracy_ontrain, acc)
     return ([x], [x_fit])

   def merge_results(a, b):
     return (a[0]+b[0], a[1]+b[1])
   res=[]
   for s in x_set:
       res.append(single_eval(s))

   #final_results = sc.parallelize(x_set).map(single_eval).reduce(merge_results)
   #print('individual num:', len(x_set))
   #print(final_results)
   return (x_set,res)


#NCS loop
def get_fit(filename):
    '''
    here is the evaluation part.
    the next work is staring here.
    '''
    # with open(work_path+'/solutions.txt','w') as f:
    #     f.write(str(X))
    f=wait_hdfs_file('/shared/work/',filename,delete=True)
    tmp_fit=np.load(f)
    os.remove(f)
    return tmp_fit
    # while True:
    #     files=os.listdir(work_path)
    #     if files == []:
    #         #print("subloop is sleeping!")
    #         time.sleep(5)
    #         continue
    #     else:
    #         for k in files:
    #             if k!=filename:
    #                 print("checking the File name.")
    #                 continue
    #             else:
    #                 print("Fitness has gotten!!")
    #                 filepath=work_path+"/"+k
    #                 tmp_fit=np.load(filepath)
    #                 os.remove(filepath)
    #                 return tmp_fit
    #         time.sleep(5)

def get_all():
    '''
    This function will get all the result in "fitX.npy",and stack them in a array.
    The result file will be deleted after read.
    In this program there will be exactly 3 result files.

    :return: [array_of_solutions,array_of_fits]
    '''

    def wait_hdfs_files(filepath,filenames,delete=False,hdfs_path="10.20.37.175",port=9000):
        flag=True
        hdfs_client=pyhdfs.HdfsClient(hdfs_path,port)
        count=len(filenames)
        res=[]
        X=[]

        while flag:
            files=hdfs_client.listdir(filepath)
            if files == []:
                time.sleep(1)
                continue
            else:
                for k in files:
                    if k in filenames:
                        f=hdfs_get_file(filepath,k,"./",delete=True)
                        tmp=np.load(f)
                        tmp_x=tmp[0]
                        tmp_fit=tmp[1]
                        res+=tmp_fit
                        X+=tmp_x
                        count-=1
            if count==0:
                return np.array([X,res])
    
    return wait_hdfs_files('/shared/work/',['fit1.npy','fit2.npy','fit3.npy'],delete=True)
                            
    #             if filename in files:
    #                 file_path=filepath+filename
    #                 f=hdfs_get_file(filepath,filename,"./",delete)
    #                 flag=False
    #             else:
    #                 time.sleep(1)
    #     print('The waited file has been retrived to local machine!')
    #     return f

    # count=0
    # res=[]
    # X=[]
    # while count<3:
    #     files=os.listdir(work_path)
    #     if files==[]:
    #         print("waiting for results")
    #     else:
    #         for k in files:
    #             if k not in ['fit1.npy','fit2.npy','fit3.npy']:
    #                 continue
    #             else:
    #                 #print("receive one result part.")
    #                 filepath=work_path+'/'+k
    #                 tmp=np.load(filepath)
    #                 #print('tmp',tmp)
    #                 tmp_x=tmp[0]
    #                 tmp_fit=tmp[1]
    #                 # print("tmp_x",tmp_x)
    #                 # print("tmp_y",tmp_fit)
    #                 for i in range(len(tmp_fit)):
    #                     res.append(tmp_fit[i])
    #                     X.append(tmp_x[i])
                    
    #                 #print('X',X)
    #                 #time.sleep(5)
    #                 count+=1
    #                 os.remove(filepath)
    #         time.sleep(5)
    # # for x in X[:3]:
    # #     print(x)
    # #print("res",res[:3])
    # return np.array([X,res])



def set_solutions(solutions):
    '''
    This function used to split solutions into 3 files, and save them into work path as a .npy file.

    :param solutions:
    :return:
    '''
    # #print(np.array(solutions).shape)
    # l=len(solutions)
    # p1=l//3
    # p2=l*2//3
    # s1=solutions[:p1]
    # s2=solutions[p1:p2]
    # s3=solutions[p2:]
    # #print(s1)
    # #print(s2)
    # #print(s3)
    # np.save(work_path+'/solutions1.npy',s1)
    # np.save(work_path+'/solutions2.npy',s2)
    # np.save(work_path+'/solutions3.npy',s3)
    # hdfs_set_file(work_path,'/shared/work/','solutions1.npy')
    # hdfs_set_file(work_path,'/shared/work/','solutions2.npy')
    # hdfs_set_file(work_path,'/shared/work/','solutions3.npy')
    # os.remove(work_path+'/solutions1.npy')
    # os.remove(work_path+'/solutions2.npy')
    # os.remove(work_path+'/solutions3.npy')
    # #np.save(work_path+'/accuracy.npy',accuracy)
    # print("files has been setted.")
    count=0
    for solution in solutions:
      fn='solution_'+str(count)+'.npy'
      np.save(fn,solution)
      hdfs_set_file('./','/shared/work/',fn)
      os.remove(fn)
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
    #thenet = caffe.Net(origin_proto_name, caffe.TEST)
    # solver.net.copy_from(work_path+'/tmp.caffemodel')
    the_input_batch=hdfs_load('/shared/work/','data.npy')
    # solver.net.blobs['data'].data[:]=the_input_batch[:]
    # print("max:",np.max(the_input_batch))
    # accuracy_ = test_net(solver.net, _count=1, _start="ip1")
    # print("accuracy_:",accuracy_)
    es = {}
    #reference_model = sc.broadcast(solver.net) ## not work, can not be pickled
    #solver.net.save(parallel_file_name) # share model by files through parallel individual
    #print(solver.net.blobs['data'].data.shape)
    #the_input_batch = sc.broadcast(solver.net.blobs['data'].data)
    #the_input_batch = sc.broadcast(solver.net.blobs['data'].data)
    
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
        _,tmp_fit = get_all()
        #_,tmp_fit = evaluate(the_input_batch, [tmp_x_], 1, accuracy_)
        #set_solutions([tmp_x_])
        # print([tmp_x_])
        # tmp=np.array([tmp_x_])
        # for i in tmp:
        #     print(i)
        # print(tmp.shape)
        # set_solutions([tmp_x_])
        # _,tmp_fit=get_all()
        es.set_initFitness(es.popsize*tmp_fit)
        print('fit:{}'.format(tmp_fit))
        print('***************NCS initialization***************')
    count=0
    while not es.stop():
        count+=1
        #print("count",count)
        if count==15:
            break
        x = es.ask()
        X = []
        for x_ in x:
            tmp_x_ = np.array(crates_list)
            for _ii in range(len(tmp_ind)):
                tmp_x_[layer_inds[tmp_ind[_ii]]] = x_[_ii]
            X.append(tmp_x_)
        # print(X)
        # tmp=np.array(X)
        # for i in tmp:
        #     print(i)
        # print(tmp.shape)
        set_solutions(X)
        X_arrange,fit=get_all()
        #np.save(work_path+'/solutions.npy',X)
        #X_arrange,fit=get_fit('fitness.npy')
        #X_arrange,fit = evaluate(the_input_batch, X, 1, accuracy_)
        #exit()
        X = []
        for x_ in X_arrange:
            tmp_x_ = np.array(len(tmp_ind)*[0.])
            for _ii in range(len(tmp_ind)):
                tmp_x_[_ii]= x_[layer_inds[tmp_ind[_ii]]] 
            X.append(tmp_x_)
        #print X,fit
        es.tell(X, fit)
        #es.disp(100)
        for _ii in range(len(tmp_ind)):
            crates_list[layer_inds[tmp_ind[_ii]]] = es.result()[0][_ii]
    for c_i in range(len(crates_list)):
        crates[layer_name[c_i]] = crates_list[c_i]
    #es_cache[itr]={'compression':-es.result()[1], 'crates':crates_list[:]}
    _tmp_c = np.array(len(crates_list)*[-1.])
    for t_name in tmp_ind:
        _tmp_c[layer_inds[t_name]] = crates[t_name]
    np.save(work_path+'/crates_list.npy',crates_list)
    # apply_prune(solver.net, crates_list)


time.sleep(3)
##--start loop:
while True:
    '''
    waiting for "ncs_start.txt" file to start work.
    when one loop is over,create a "fitness_over.txt" file in work path.
    '''
    f=wait_hdfs_file('/shared/work/','ncs_start.txt',delete=False)
    with open(f,'r') as ff:
      msg=ff.read()
      if msg=='exit':
        exit()
      else:
        msg=eval(msg)
        tmp_crates=msg[0]
        tmp_ind=msg[1]
        tmp_accuracy_=hdfs_load('/shared/work/','accuracy.npy')
      NCSloop(tmp_crates,tmp_ind,tmp_accuracy_)
      print("NCSloop is completed!")
      os.remove(f)
      with open('ncs_over.txt','w') as ff:
        ff.write('complete!')
      hdfs_set_file('./','/shared/work/','ncs_over.txt')
      
    # files=os.listdir(work_path)
    # if files == []:
    #     #print("NCSLoop is sleeping!")
    #     time.sleep(10)
    #     continue
    # else:
    #     for k in files:
    #       if k!='ncs_start.txt':
    #         #print("Outloop checking the File name.")
    #         continue
    #       else:
    #         filepath=work_path+"/"+k
    #         with open(filepath,'r') as f:
    #             msg=f.read()
    #             if msg=='exit':
    #                 with open(work_path+'/fitness_over.txt','w') as ff:
    #                     ff.write('exit')
    #                 exit()
    #             msg=eval(msg)
    #             tmp_crates=msg[0]
    #             tmp_ind=msg[1]
    #             tmp_accuracy_=np.load(work_path+'/accuracy.npy')
    #         NCSloop(tmp_crates,tmp_ind,tmp_accuracy_)
    #         print("NCSloop is completed!")
    #         os.remove(filepath)
    #         with open(work_path+'/ncs_over.txt','w') as f:
    #             f.write('complete!')
    #     time.sleep(5)