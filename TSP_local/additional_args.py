import argparse
import sys

def get_args():
   print(sys.argv)
   parse = argparse.ArgumentParser(description="arguments for the demo")
   parse.add_argument('--master_ip_list', required=True, type=str)
   parse.add_argument('--master_port_list', required=True, type=str)
   parse.add_argument('--worker_ip_list', type=str)
   parse.add_argument('--worker_port_list', type=str)
   parse.add_argument('--task_role_index', type=int)
   return parse.parse_args()
