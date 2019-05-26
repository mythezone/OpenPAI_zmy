# encoding=utf-8
import numpy as np
import time
class Func(object):
    def __init__(self,optimal_solution,bias=0):
        self.dimension = len(optimal_solution)
        self.optimal_solution = np.array(optimal_solution)
        self.bias = bias

        #print("The best solution:", self.optimal_solution)
        print("The best fitness:", self.evaluate(self.optimal_solution))

    def evaluate(self,solution):
        pass

class Func1(Func):

    def evaluate(self,solution):
        solution=np.array(solution)
        z=solution-self.optimal_solution
        return np.sum(z*z)+self.bias

class Func1_backup(object):
    def __init__(self, optimal_solution, bias=0):
        self.dimension=len(optimal_solution)
        self.optimal_solution=np.array(optimal_solution)
        self.bias=bias

        print("The best solution:",self.evaluate(self.optimal_solution))


    def evaluate(self,solution):
        solution=np.array(solution)
        z=solution-self.optimal_solution
        return np.sum(z*z)+self.bias

class Func2(object):
    def __init__(self, optimal_solution, bias=0):
        self.dimension = len(optimal_solution)
        self.optimal_solution = np.array(optimal_solution)
        self.bias = bias

        print("The best solution of Function2:", self.evaluate(self.optimal_solution))
        self.dimension=len(self.optimal_solution)


    def evaluate(self,solution):
        solution=np.array(solution)
        z=solution-self.optimal_solution

        temp = 0
        res = 0
        for i in range(self.dimension):
            temp+=z[i]
            res+=pow(temp,2)

        return res+self.bias

class Func3(Func):
    def evaluate(self,solution):
        z=solution-self.optimal_solution
        for i in range(self.dimension):
            z[i]=(10e6)**((i)/(self.dimension-1))*z[i]**2
        res=np.sum(z)+self.bias
        return res

class Func4(Func):
    def evaluate(self,solution):
        z=solution-self.optimal_solution
        res=0
        for i in range(self.dimension):
            tmp=0
            for j in range(i+1):
                tmp+=z[j]**2
            res+=tmp
        res*=(1+0.4*abs(np.random.normal(0,1)))
        res+=self.bias
        return res

class Func5(Func):
    def evaluate(self,solution):
        #time.sleep(1)
        A=np.random.randint(-500,500,(self.dimension,self.dimension))
        o=np.random.uniform(-100,100,self.dimension)
        B=[]
        z=[]
        for i in range(self.dimension):
            B.append(np.dot(A[i],o))
        for i in range(self.dimension):
            z.append(np.dot(A[i],o)-B[i])

        res=np.max(z)
        return res+self.bias



class Func6(object):
    def __init__(self, optimal_solution, bias=0):
        self.dimension = len(optimal_solution)
        self.optimal_solution = np.array(optimal_solution)
        self.bias = bias

        print("The best solution of Function6:", self.evaluate(self.optimal_solution))
        self.dimension=len(self.optimal_solution)

    def evaluate(self,solution):

        res=0
        z=solution-self.optimal_solution+1

        for i in range(self.dimension-1):
            res+=100*((z[i]**2-z[i+1])**2)+(z[i]-1)**2

        res+=self.bias
        return res


class Func7(Func):
    '''
    F 7 : Shifted Rotated Griewank’s Function without Bounds
    '''
    def evaluate(self,solution):
        res=0
        res2=1
        z=solution-self.optimal_solution
        for i in range(self.dimension):
            res+=z[i]**2/4000
            res2*=np.cos(z[i]/(i+1)**0.5)
        res=res-res2+1+self.bias
        return res

class Func8(Func):
    '''
    Shifted Rotated Ackley’s Function with Global Optimum on Bounds
    '''

    def evaluate(self,solution):
        solution=solution-self.optimal_solution
        _tmp=-20*np.exp(-0.2*((1/self.dimension)*np.sum(solution**2))**0.5)
        _tmp-=np.exp(1/self.dimension*np.sum(np.cos(2*np.pi*solution)))
        _tmp+=20+np.e+self.bias
        return _tmp

class Func9(Func):
    '''
    F 9 : Shifted Rastrigin’s Function
    '''
    def evaluate(self,solution):
        solution=solution-self.optimal_solution
        res=np.sum(solution**2-10*np.cos(2*np.pi*solution)+10)+self.bias
        return res

class Func10(Func):
    '''
    F 10 : Shifted Rotated Rastrigin’s Function
    '''
    def evaluate(self,solution):
        solution=solution-self.optimal_solution
        res=np.sum(solution**2-10*np.cos(2*np.pi*solution)+10)+self.bias
        return res

class Func11(Func):
    '''
    F 11 : Shifted Rotated Weierstrass Function
    '''
    def evaluate(self,solution):
        a=0.5
        b=3
        kmax=20
        z=solution-self.optimal_solution
        res=[0 for i in range(self.dimension)]
        for i in range(kmax):
            res+=a**i*np.cos(2*np.pi*b**i*(z+0.5))
        res=np.sum(res)-self.dimension*(np.sum([a**i*np.cos(2*np.pi*b**i*0.5) for i in range(kmax)]))
        return res+self.bias

class Func12():
    '''
    F 12 : Schwefel’s Problem 2.13
    '''
    def __init__(self,optimal_solution,bias=0):
        self.dimension = len(optimal_solution)
        self.optimal_solution = np.array((optimal_solution-np.min(optimal_solution))/(np.max(optimal_solution)-np.min(optimal_solution))*2*np.pi)
        self.bias = bias
        self.A = np.random.randint(-100, 100, (self.dimension, self.dimension))
        self.B = np.random.randint(-100, 100, (self.dimension, self.dimension))
        self.alpha = self.optimal_solution
        # print("The best solution:", self.optimal_solution)
        print("The best fitness:", self.evaluate(self.optimal_solution))
        print(self.alpha)
        print(self.A)

    def evaluate(self,solution):

        vectorA=np.array([self.A[i]*np.sin(self.alpha[i])+self.B[i]*np.cos(self.alpha[i]) for i in range(self.dimension)])
        vectorB=np.array([self.A[i]*np.sin(solution[i]+self.B[i]*np.cos(solution[i])) for i in range(self.dimension)])
        res=np.sum((vectorA-vectorB)**2)+self.bias
        return res
