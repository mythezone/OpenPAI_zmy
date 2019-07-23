def generate_log_func(log_type, file_name):
   LOG_TYPE=log_type # only 'file' and 'print' reserved
   FILE_NAME = file_name

   def log_info(*info_str):
        if LOG_TYPE == 'file':
          with open(FILE_NAME, 'a+') as fi:
             fi.write(str(info_str))
             fi.write('\n')
        elif LOG_TYPE == 'print':
          print(info_str)
        else:
          pass
   return log_info
