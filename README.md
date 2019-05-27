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
   4. 将3中所得的循环次数加上已经循环的次数,如果大于tmax则判断为已完成,回到步骤2

2. LoopTest1任务:
   1. 