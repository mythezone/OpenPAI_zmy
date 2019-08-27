# CNN 容器化过程



## CNN单机容器demo

1. 使用219服务器上的 lgy/spark_gpu:test 镜像

2. 将CNN_docker_python2 文件夹中的内容打包拷贝到镜像中构建Dockerfile内容如下：

   ```dockerfile
   FROM lgy/spark_gpu:test
   MAINTAINER Muyao Zhong
   
   COPY CNN_docker_python2.tar /
   RUN cd / && tar -xzf CNN_docker_python2.tar && cd CNN_docker_python2
   WORKDIR /CNN_docker_python2
   ```

3. 使用docker build构建image

4. ```
   docker build -t mythezone/cnn_microservice:v1 .
   ```

   使用以下命令分别运行master.py，loop1.py, loop2.py, evaluator.py, main.py

5. ```
   docker run -ti --network=host --name cnn_master mythezone/cnn_microservice:v6 python master.py
   
   nvidia-docker run -ti --network=host --name cnn_loop1 mythezone/cnn_microservice:v6 python loop1.py
   
   docker run -ti --network=host --name cnn_loop2 mythezone/cnn_microservice:v6 python loop2.py
   
   nvidia-docker run -ti --network=host --name cnn_evaluator mythezone/cnn_microservice:v6 python evaluator.py
   
   docker run -ti --network=host --name cnn_main mythezone/cnn_microservice:v6 python main.py
   
   ```