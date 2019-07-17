from tqdm import tqdm
import time

if __name__=="__main__":
    for i in tqdm(range(10000)):
        time.sleep(0.1)