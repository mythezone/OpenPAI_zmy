现在碰到一个问题.关于TSP的demo已经可以在PAI上运行(spark的local模式下).但是如果spark的--master设置为yarn就会出现
```
2019-06-18 08:53:24 INFO  Client:54 - Application report for application_1558351089344_0243 (state: FAILED)
2019-06-18 08:53:24 INFO  Client:54 - 
	 client token: N/A
	 diagnostics: Application application_1558351089344_0243 failed 2 times due to AM Container for appattempt_1558351089344_0243_000002 exited with  exitCode: 13
Failing this attempt.Diagnostics: [2019-06-18 08:53:21.308]Exception from container-launch: 
ExitCodeException exitCode=13: Error: No such object: container_e14_1558351089344_0243_02_000001
Error: No such object: container_e14_1558351089344_0243_02_000001
```
这个错误.

主要任务配置如下:
```
"command": "git clone https://github.com/mythezone/OpenPAI_zmy.git   && cd OpenPAI_zmy/TSP_on_PAI  &&  \
spark-submit --master yarn --deploy-mode cluster --driver-memory 5g --executor-memory 6g \
--executor-cores 11  --num-executors=2  --archives hdfs://10.20.37.175:9000/Python/Python.zip#Python  \
--conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=/usr/bin/python3.5  tsp_loop.py",
```

部分日志:
```
2019-06-18 08:51:34 INFO  Client:54 - Source and destination file systems are the same. Not copying hdfs://10.20.37.175:9000/Python/Python.zip#Python
2019-06-18 08:51:34 INFO  Client:54 - Uploading resource file:/OpenPAI_zmy/TSP_on_PAI/tsp_loop.py -> hdfs://10.20.37.175:9000/user/admin/.sparkStaging/application_1558351089344_0243/tsp_loop.py
2019-06-18 08:51:34 INFO  Client:54 - Uploading resource file:/spark-example/spark-2.3.1-bin-hadoop2.7/python/lib/pyspark.zip -> hdfs://10.20.37.175:9000/user/admin/.sparkStaging/application_1558351089344_0243/pyspark.zip
2019-06-18 08:51:34 INFO  Client:54 - Uploading resource file:/spark-example/spark-2.3.1-bin-hadoop2.7/python/lib/py4j-0.10.7-src.zip -> hdfs://10.20.37.175:9000/user/admin/.sparkStaging/application_1558351089344_0243/py4j-0.10.7-src.zip
2019-06-18 08:51:34 INFO  Client:54 - Uploading resource file:/tmp/spark-73aaffbd-2f31-4b5d-8b50-b51596a51081/__spark_conf__4228533599827062925.zip -> hdfs://10.20.37.175:9000/user/admin/.sparkStaging/application_1558351089344_0243/__spark_conf__.zip
2019-06-18 08:51:34 INFO  SecurityManager:54 - Changing view acls to: root,admin
2019-06-18 08:51:34 INFO  SecurityManager:54 - Changing modify acls to: root,admin
2019-06-18 08:51:34 INFO  SecurityManager:54 - Changing view acls groups to: 
2019-06-18 08:51:34 INFO  SecurityManager:54 - Changing modify acls groups to: 
2019-06-18 08:51:34 INFO  SecurityManager:54 - SecurityManager: authentication disabled; ui acls disabled; users  with view permissions: Set(root, admin); groups with view permissions: Set(); users  with modify permissions: Set(root, admin); groups with modify permissions: Set()
2019-06-18 08:51:34 INFO  Client:54 - Submitting application application_1558351089344_0243 to ResourceManager
2019-06-18 08:51:35 INFO  YarnClientImpl:273 - Submitted application application_1558351089344_0243
2019-06-18 08:51:36 INFO  Client:54 - Application report for application_1558351089344_0243 (state: ACCEPTED)
2019-06-18 08:51:36 INFO  Client:54 - 
	 client token: N/A
	 diagnostics: AM container is launched, waiting for AM container to Register with RM
	 ApplicationMaster host: N/A
	 ApplicationMaster RPC port: -1
	 queue: default
	 start time: 1560847894950
	 final status: UNDEFINED
	 tracking URL: http://10.20.37.175:8088/cluster/app/application_1558351089344_0243/
	 user: admin
2019-06-18 08:51:37 INFO  Client:54 - Application report for application_1558351089344_0243 (state: ACCEPTED)
```

在这个ACCEPTED状态一直等待到出现ERROR.

请问你们之前有没有碰到过这个问题?有什么解决的办法?