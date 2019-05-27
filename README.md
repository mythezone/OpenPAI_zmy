# OpenPAI_zmy

## 本demo包括四个Job:
1. main1
2. LoopTest1
3. LoopTest2
4. single_threading1

其逻辑为:
1. main1 任务:
   1. 在hdfs的/shared/文件夹中清空(或创建)work文件夹
   2. 在work文件夹中创建new_itr.txt文件并写入循环数(如果已经完成将写入'over'字符串,并结束)
   3. 等待report.txt文件(该文件中为已经完成的循环次数)
   4. 将3中所得的循环次数加上已经循环的次数,如果大于tmax则判断为已完成,回到步骤ii
   
    ```json
    {
    "jobName": "test1-main-zmy-001_runable_fdasf",
    "image": "registry.cn-hangzhou.aliyuncs.com/lgy_sustech/olmp:v2",
    "virtualCluster": "default",
    "taskRoles": [
        {
        "name": "main",
        "taskNumber": 1,
        "cpuNumber": 2,
        "memoryMB": 8192,
        "gpuNumber": 0,
        "command": "git clone https://github.com/mythezone/OpenPAI_zmy.git   && cd OpenPAI_zmy&&chmod 777 * &&  python main1.py "
        }
    ]
    }
    ```

2. LoopTest1任务:
   1. 对神经网络进行训练,得到原始的神经网络data,accuracy,生成初始solution并写入work文件夹中
   2. 等待work文件夹中的new_itr.txt文件
   3. 如果文件内容为over就结束,否则继续
   4. 在work文件夹下生成ncs_start.txt文件,调用内层循环计算神经网络剪枝的solution,并使用solution神经网络进行压缩
   5. 将已经循环的次数写入report.txt文件,回到步骤ii

    ```json
    {
    "jobName": "test1-LoopTest1-zmy-002_runable_fdafd",
    "image": "registry.cn-hangzhou.aliyuncs.com/lgy_sustech/olmp:v2",
    "virtualCluster": "default",
    "taskRoles": [
        {
        "name": "main",
        "taskNumber": 1,
        "cpuNumber": 4,
        "memoryMB": 8192,
        "gpuNumber": 1,
        "command": "git clone https://github.com/mythezone/OpenPAI_zmy.git  && cd OpenPAI_zmy&&chmod 777 * &&  python LoopTest1.py "
        }
    ]
    }
    ```


3. LoopTest2
   1. 该循环获取ncs_start.txt文件后开始工作
   2. 获取work文件夹下的一些必要的数据后开始ncs初始化和训练.
   3. 将初始化的solutions分解成n单个的solution并存入hdfs上work文件夹中,文件名为solution_XXXXXX.npy
   4. 等待n个文件名为fit_solutions_XXXXXXX.npy文件中的结果,合并后进行ncs训练
   5. 将结果写入crates_list.npy文件.并创建ncs_over.txt文件,回到步骤i
    ```json
    {
    "jobName": "test1-LoopTest2-zmy-003_runable_dfafda",
    "image": "registry.cn-hangzhou.aliyuncs.com/lgy_sustech/olmp:v2",
    "virtualCluster": "default",
    "taskRoles": [
        {
        "name": "main",
        "taskNumber": 1,
        "cpuNumber": 4,
        "memoryMB": 8192,
        "gpuNumber": 0,
        "command": "git clone https://github.com/mythezone/OpenPAI_zmy.git  && cd OpenPAI_zmy&&chmod 777 * &&  python LoopTest2.py "
        }
    ]
    }
    ```


4. single_threading1
   1. 该任务等待solution_XXXXXX.npy文件
   2. 获得该类文件后,计算fitness值,将结果写入fit_solution_XXXXXXX.npy文件,并删除原solution文件
   3. 回到步骤i

    ```json
    {
    "jobName": "test1-single_evaluate-zmy-004_runable",
    "image": "registry.cn-hangzhou.aliyuncs.com/lgy_sustech/olmp:v2",
    "virtualCluster": "default",
    "taskRoles": [
        {
        "name": "main",
        "taskNumber": 1,
        "cpuNumber": 4,
        "memoryMB": 8192,
        "gpuNumber": 1,
        "command": "git clone https://github.com/mythezone/OpenPAI_zmy.git  && cd OpenPAI_zmy&&chmod 777 *  &&  python single_threading1.py "
        }
    ]
    }
    ```
    