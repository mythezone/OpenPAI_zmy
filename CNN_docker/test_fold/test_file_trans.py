import socket
import os
import hashlib

server = socket.socket()

server.bind(("localhost", 10012)) # 绑定监听端口

server.listen(5)  # 监听

print("监听开始..")

while True:
    conn, addr = server.accept()  # 等待连接

    print("conn:", conn, "\naddr:", addr)  # conn连接实例

    while True:
        data = conn.recv(1024)  # 接收
        if not data:  # 客户端已断开
            print("客户端断开连接")
            break

        print("收到的命令：", data.decode("utf-8"))
        cmd, filename = data.decode("utf-8").split(" ")
        if cmd =="get":
            if os.path.isfile(filename):  # 判断文件存在

                # 1.先发送文件大小，让客户端准备接收
                size = os.stat(filename).st_size  #获取文件大小
                conn.send(str(size).encode("utf-8"))  # 发送数据长度
                print("发送的大小：", size)

                # 2.发送文件内容
                conn.recv(1024)  # 接收确认

                m = hashlib.md5()
                f = open(filename, "rb")
                for line in f:
                    conn.send(line)  # 发送数据
                    m.update(line)
                f.close()

                # 3.发送md5值进行校验
                md5 = m.hexdigest()
                conn.send(md5.encode("utf-8"))  # 发送md5值
                print("md5:", md5)


server.close()
# --------------------- 
# 作者：彭世瑜 
# 来源：CSDN 
# 原文：https://blog.csdn.net/mouday/article/details/79101951 
# 版权声明：本文为博主原创文章，转载请附上博文链接！