import base_util as bu

if __name__=="__main__":
    wkr=bu.worker('loop',lambda x:x)
    wkr.run()