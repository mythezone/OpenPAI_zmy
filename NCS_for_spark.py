# coding=utf-8
import numpy as np
import matplotlib.pyplot as plt
#from pyspark import SparkContext
from pyspark.context import SparkContext
import CEC2005Functions as func
sc=SparkContext()
import time


def Bhattacharyya_distance(vector1, vector2, sigema1, sigema2):
    v1, v2 = np.array(vector1), np.array(vector2)
    l = len(v1)
    # db=0.125*np.sum(v1*v2*((sigema1+sigema2)/2))+0.5*l*np.log((sigema1+sigema2)/sigema1/sigema2)
    db = 0.125 * np.sum(v1 * v2 / ((sigema1 + sigema2) * 2)) + 0.5 * l * (
                np.log(0.5 * (sigema1 + sigema2)) - 0.5 * np.log(sigema1) - 0.5 * np.log(sigema2))
    return db

def cal_dist(solutions,sigema):
    def function(s):
        dist = 999999999999999
        for i in range(len(solutions)):

            if s[0]==i:
                continue
            db=Bhattacharyya_distance(s[1],solutions[i],sigema[s[0]],sigema[i])
            if db<dist:
                dist=db
        return db
    return function

class NCS(object):
    def __init__(self,times=2,index=6,dimension=4,upbord=100,lowbord=-100,epoch=20,sigema=1.0,r=0.99,population=50,t_max=1000):
        #按照需要初始化问题
        self.epoch=epoch
        self.sig=sigema
        self.r=r
        self.population=int(population)
        self.t_max=t_max
        self.upbord=upbord
        self.lowbord=lowbord
        self.dimension=dimension
        self.index=int(index)
        self.times=times
        self.res=[]
        info = "Infomation of the Problem:\n" \
               "the algorithm will run %d times\n" \
               "fitness function use the %d-th in CEC2005\n" \
               "dimension of the solution space is %d\n" \
               "scale of the space is %f to %f \n" \
               "epoch is %d\n" \
               "init sigema is %f\n" \
               "population of the EA is %d\n" \
               "max generation is %d\n" % (
               self.times, self.index, self.dimension, self.upbord, self.lowbord, self.epoch, self.sig,
               self.population, self.t_max)
        print(info)
        self.run_NCS(times)
        #times_costed=np.array(self.loop_time_cost)

        print("total time is :",self.time_in_total)
        print("time for fitness is :",self.time_for_fitness)
        print("time for distance is : ",self.time_for_distance)

        #plt.show()

    def init(self):
        self.t=0

        # 建立Fitness Function以及确定最优解,以及evaluate方法
        # 目前只使用了Function1作为默认的问题，待修改为可以自主选择版本
        self.optimal_solution = np.random.uniform(self.lowbord, self.upbord, self.dimension)
        self.f = eval("func.Func" + str(self.index) + "(self.optimal_solution)")
        self.evaluate = self.f.evaluate

        # 以下是初始化种群，变异参数以及距离计算量，和是否替换的flag
        self.solutions = np.random.uniform(self.lowbord, self.upbord, (self.population, self.dimension))
        self.solutions_next = self.solutions.copy()
        self.sigema = np.array([self.sig for i in range(self.population)])
        self.fitnesses = np.zeros(self.population)
        self.fitnesses_next = np.zeros(self.population)
        self.distances = np.zeros(self.population)

        self.distances_next = np.zeros(self.population)
        self.changed = np.zeros(self.population)
        self.flag = np.zeros(self.population)

        self.calculate_all_fitness()
        self.best_index = self.find_best(self.fitnesses)
        self.best_fitness = self.fitnesses[self.best_index]
        self.best_solution = self.solutions[self.best_index]
        #记录每个loop使用了多长时间
        #self.loop_time_cost=[]
        self.time_for_fitness=0
        self.time_for_distance=0
        self.time_in_total=0


    def draw(self):
        plt.scatter(self.solutions[:, 0], self.solutions[:, 1])

    def run_NCS(self,times=1,method=1):
        if method==1:
            for i in range(times):
                self.init()
                self.loop()


    def loop(self):
        #plt.figure()
        print("start")
        T=0
        while self.t<self.t_max:
            start=time.time()

            self.map_function=cal_dist(self.solutions,self.sigema)
            self.map_next_function=cal_dist(self.solutions_next,self.sigema)
            self.lamb = np.random.normal(1, 0.1 - 0.1 * (self.t / self.t_max))

            #计算各个操作所需时间。
            t1=time.time()
            self.calculate_all_distance()
            t2=time.time()
            self.calculate_all_fitness()
            self.next_solutions()
            self.calculate_all_fiteness_next()
            t4=time.time()
            self.calculate_all_distance_next()
            t5=time.time()

            self.time_for_distance+=t2-t1+t5-t4
            self.time_for_fitness+=t4-t2
            self.normalization()
            index = self.find_best(self.fitnesses_next)
            if self.fitnesses_next[index] < self.best_fitness:
                self.best_fitness = self.fitnesses_next[index]
                self.best_index = index
                self.best_solution = self.solutions_next[index]
            self.flag_generator()
            self.next_generation()
            # print("the flag",self.flag)
            self.t += 1
            # print("solution:",self.solutions)
            # print("solution_next:",self.solutions_next)
            if self.t % self.epoch == 0:
                # print("normalized fitness",self.fitnesses_next[:5])
                # print("normalized distance",self.distances_next[:5])
                self.sigema_update()
                # print("the sigema:",self.sigema)
                self.res.append(np.average(self.fitnesses))
                #self.draw()
            end=time.time()
            #self.loop_time_cost.append(end-start)
            self.time_in_total+=end-start

        print("The best fitness has been finded by NCS is :",self.best_fitness)

    # def tradition_loop(self):
    #     while self.t<self.t_max:
    #         self.calculate_all_fitness()
    #         self.next_solutions()
    #         self.calculate_all_fiteness_next()
    #         self.random_select(2)
    #         index = self.find_best(self.fitnesses_next)
    #         if self.fitnesses_next[index] < self.best_fitness:
    #             self.best_fitness = self.fitnesses_next[index]
    #             self.best_index = index
    #             self.best_solution = self.solutions_next[index]
    #         self.flag[self.best_index]=True
    #         self.next_generation()
    #         self.t+=1
    #         if self.t%20==0:
    #             self.draw()
    #     print("In tradition model best solution is :",self.best_solution,self.best_index,self.best_fitness)


    def find_best(self,arr):
        best_index=np.argmin(arr)
        return best_index

    def calculate_all_fitness(self):
        rdd1=sc.parallelize(self.solutions)
        tmp=rdd1.map(self.evaluate)
        self.fitnesses=np.array(tmp.collect())
        return

    def calculate_all_fiteness_next(self):
        rdd1 = sc.parallelize(self.solutions_next)
        tmp = rdd1.map(self.evaluate)
        self.fitnesses_next = np.array(tmp.collect())
        return

    def Bhattacharyya_distance(self,vector1,vector2,sigema1,sigema2):
        v1,v2=np.array(vector1),np.array(vector2)
        l=len(v1)
        #db=0.125*np.sum(v1*v2*((sigema1+sigema2)/2))+0.5*l*np.log((sigema1+sigema2)/sigema1/sigema2)
        db=0.125*np.sum(v1*v2/((sigema1+sigema2)*2))+0.5*l*(np.log(0.5*(sigema1+sigema2))-0.5*np.log(sigema1)-0.5*np.log(sigema2))
        return db



    def calculate_all_distance(self):
        '''
        利用spark计算下一代个体与其他个体之间距离的最小值
        map传入的函数是由函数工厂生成的含有当前所有父代信息和当前sigema值的函数
        该函数接受一个solution作为参数，返回该solution的distance
        :return:
        '''
        tmp_rdd=sc.parallelize(zip([i for i in range(self.population)],self.solutions))
        tmp_dist=tmp_rdd.map(self.map_function)
        self.distances=np.array(tmp_dist.collect())


    def calculate_all_distance_next(self):
        '''
        利用spark计算下一代个体与其他个体之间距离的最小值
        map传入的函数是由函数工厂生成的含有当前所有父代信息和当前sigema值的函数
        该函数接受一个solution作为参数，返回该solution的distance
        :return:
        '''
        tmp_rdd = sc.parallelize(zip([i for i in range(self.population)], self.solutions_next))
        tmp_dist = tmp_rdd.map(self.map_next_function)
        self.distances_next = np.array(tmp_dist.collect())


    def find_index(self,arr):
        '''
        寻找当前种群中最佳fitness个体的index
        :param arr:
        :return:
        '''
        best=100000000
        index=-1
        for i in range(len(arr)):
            if arr[i]<best:
                best=arr[i]
                index=i
        return index

    def next_solutions(self,index=-1):
        '''
        基于所给顶的solution的index，生成一个随机新solution加入solutions_next
        :param solution:
        :return: new solution
        '''
        if index==-1:
            #如果index为-1，就生成全部的下一代解
            for i in range(self.population):
                step=np.random.normal(0,self.sigema[i],self.dimension)
                self.solutions_next[i]=self.solutions[i]+step
        else:
            step=np.random.normal(0,self.sigema[index],self.dimension)
            self.solutions_next[index]=self.solutions[index]+step

        return



    # def change_sigema(self,c):
    #     '''
    #     该函数可以根据c的大小更新sigema的值
    #     1/5 successful rule
    #
    #     ps：在论文中的r小于1.0，在更新时要放大应当除以r，但是文中使用乘以r，此处存疑
    #     :param c: 在本次迭代中更换的solution数量
    #     :return:
    #     '''
    #     flag=c/self.epoch
    #     if flag==0.2:
    #         pass
    #     elif flag>0.2:
    #         self.sigema/=self.r
    #     else:
    #         self.sigema*=self.r
    #     return

    def fifth(self,c):
        if c/self.epoch==0.2:
            return 1
        elif c/self.epoch<0.2:
            return self.r
        else:
            return 1/self.r

    def sigema_update(self):
        for i in range(self.population):
            self.sigema[i]*=self.fifth(self.changed[i])


    def normalization(self):
        '''
        归一化fitness和distance
        :return:
        '''
        self.fitnesses_next=self.fitnesses_next/(self.fitnesses+self.fitnesses_next+0.000001)
        self.distances_next=self.distances_next/(self.distances+self.distances_next+0.000001)

    def flag_generator(self):
        self.flag = self.fitnesses_next / self.distances_next < self.lamb

    def next_generation(self):

        '''
        基于fitness和distance的比较丢弃较差的解，并产生下一代解
        :return:
        '''

        for i in range(self.population):
            if self.flag[i]==True:
                self.solutions[i]=self.solutions_next[i]
                self.changed[i]+=1
            else:
                pass

    def random_select(self,index=1):
        if index==1:
            self.flag=[np.random.rand()>0.5 for i in range(self.population)]
        elif index==2:
            self.flag=self.fitnesses>self.fitnesses_next

    def next_step(self):
        pass


if __name__ == "__main__":
    ncs=NCS(1,5,3,100,-100,20,1.0,.99,20,500)
    print("the final result is :",ncs.best_fitness)
    # solution=[1.0,2.0,3.0]
    # sigema=1.0
    # #print("solutions:\n",ncs.solutions)
    # #print("solutions_next:\n",ncs.solutions_next)
    # #print("changed;\n",ncs.changed)
    # #print("distance:\n",ncs.distances)
    # # print("fitness:\n",ncs.fitnesses)
    # # ncs.calculate_all_fitness()
    # # print("fitness:\n",ncs.fitnesses)
    # ncs.calculate_all_distance()
    # ncs.next_solutions()
    # ncs.calculate_all_fitness()
    # ncs.calculate_all_fiteness_next()
    # ncs.calculate_all_distance_next()
    # ncs.normalization()
    # ncs.next_generation()
    # print("distance:\n",ncs.distances_next)
    # print("fitness:\n",ncs.fitnesses_next)
