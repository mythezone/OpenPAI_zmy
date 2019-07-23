# TSP demo with TCP communication On OpenPAI

## How to use:
1. use this config file 
```json
{
  "jobName": "TSP_demo_container_test_c8f0402c",
  "image": "registry.cn-hangzhou.aliyuncs.com/lgy_sustech/tsp_microservice:v1",
  "virtualCluster": "default",
  "taskRoles": [
    {
      "name": "test_master",
      "taskNumber": 1,
      "cpuNumber": 1,
      "memoryMB": 100,
      "gpuNumber": 0,
      "command": "cd ~/ && git clone https://github.com/IdiosyncraticDragon/OpenPAI_zmy.git && cd ~/OpenPAI_zmy/TSP_local/ && git checkout OpenPAI_TSP && python test_master.py --master_ip_list $PAI_HOST_IP_test_master_0  --master_port_list $PAI_PORT_LIST_test_master_0_master_port",
      "portList": [
        {
          "label": "master_port",
          "beginAt": 0,
          "portNumber": 1
        }
      ]
    },
    {
      "name": "test_worker1",
      "taskNumber": 1,
      "cpuNumber": 1,
      "memoryMB": 100,
      "gpuNumber": 0,
      "command": "cd ~/ && git clone https://github.com/IdiosyncraticDragon/OpenPAI_zmy.git && cd ~/OpenPAI_zmy/TSP_local/ && git checkout OpenPAI_TSP && python test_loop.py --master_ip_list $PAI_HOST_IP_test_master_0 --master_port_list $PAI_PORT_LIST_test_master_0_master_port --worker_ip_list $PAI_CONTAINER_HOST_IP  --worker_port_list $PAI_CONTAINER_HOST_worker1_port_PORT_LIST --task_role_index $PAI_CURRENT_TASK_ROLE_CURRENT_TASK_INDEX",
      "portList": [
        {
          "label": "worker1_port",
          "beginAt": 0,
          "portNumber": 1
        }
      ],
      "minSucceededTaskCount": 1
    },
    {
      "name": "test_worker2",
      "taskNumber": 1,
      "cpuNumber": 1,
      "memoryMB": 100,
      "gpuNumber": 0,
      "command": "cd ~/ && git clone https://github.com/IdiosyncraticDragon/OpenPAI_zmy.git && cd ~/OpenPAI_zmy/TSP_local/ && git checkout OpenPAI_TSP && python test_iteration.py --master_ip_list $PAI_HOST_IP_test_master_0 --master_port_list $PAI_PORT_LIST_test_master_0_master_port --worker_ip_list $PAI_CONTAINER_HOST_IP --worker_port_list $PAI_CONTAINER_HOST_worker2_port_PORT_LIST --task_role_index $PAI_CURRENT_TASK_ROLE_CURRENT_TASK_INDEX",
      "portList": [
        {
          "label": "worker2_port",
          "beginAt": 0,
          "portNumber": 1
        }
      ]
    },
    {
      "name": "test_worker3",
      "taskNumber": 1,
      "cpuNumber": 1,
      "memoryMB": 100,
      "gpuNumber": 0,
      "command": "cd ~/ && git clone https://github.com/IdiosyncraticDragon/OpenPAI_zmy.git && cd ~/OpenPAI_zmy/TSP_local/ && git checkout OpenPAI_TSP && python test_init.py --master_ip_list $PAI_HOST_IP_test_master_0 --master_port_list $PAI_PORT_LIST_test_master_0_master_port --worker_ip_list $PAI_CONTAINER_HOST_IP --worker_port_list $PAI_CONTAINER_HOST_worker3_port_PORT_LIST --task_role_index $PAI_CURRENT_TASK_ROLE_CURRENT_TASK_INDEX",
      "portList": [
        {
          "label": "worker3_port",
          "beginAt": 0,
          "portNumber": 1
        }
      ]
    }
  ],
  "jobEnvs": {
    "isDebug": true
  }
}
```
2. run the json config on the openPAI.
3. check the ip and ssh port of the worker3 (which is the test_init.py)
4. follow the description in the `ssh info` which is belong to the item of test_worker3
5. login the the test_worker3 container
```bash
$> cd OpenPAI_TSP/TSP_local
```
6. check the component inside loop.txt to verify whehter the program is finished.
