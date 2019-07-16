import numpy as np
import json
from functools import partial
import time
import sys,os
from func_lib import message

func1=lambda x,ob=None:ob.recv_list.put(message(1,x*2).msg_encode())
func2=lambda x,ob=None:ob.recv_list.put(message(2,x*3).msg_encode())
func3=lambda x,ob=None:ob.recv_list.put(message(3,x*5).msg_encode())

def get_dct():
    funcs=dict()
    funcs[0]=func1
    funcs[1]=func2
    funcs[2]=func3
    return funcs

