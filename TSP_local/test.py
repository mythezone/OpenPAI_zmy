import json

with open("task_config.json",'r') as f:
    tmp=json.loads(f.read())
    print(tmp)
    print(tmp['process']['0'])