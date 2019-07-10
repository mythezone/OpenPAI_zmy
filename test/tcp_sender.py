from socket import *
import struct
import json
import os

tcp_server = socket(AF_INET, SOCK_STREAM)
ip_port = (('127.0.0.1', 8080))
buffsize = 1024

#   端口的重复利用
tcp_server.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
tcp_server.bind(ip_port)
tcp_server.listen(5)
print('还没有人链接')
while True:
    '''链接循环'''
    conn, addr = tcp_server.accept()

    print('链接人的信息:', addr)
    while True:
        if not conn:
            print('客户端链接中断')
            break
        '''通信循环'''
        filemesg = input('请输入要传送的文件名加后缀>>>').strip()

        filesize_bytes = os.path.getsize(filemesg) # 得到文件的大小,字节
        filename = 'new' + filemesg
        dirc = {
            'filename': filename,
            'filesize_bytes': filesize_bytes,
        }
        head_info = json.dumps(dirc)  # 将字典转换成字符串
        head_info_len = struct.pack('i', len(head_info)) #  将字符串的长度打包
        #   先将报头转换成字符串(json.dumps), 再将字符串的长度打包
        #   发送报头长度,发送报头内容,最后放真是内容
        #   报头内容包括文件名,文件信息,报头
        #   接收时:先接收4个字节的报头长度,
        #   将报头长度解压,得到头部信息的大小,在接收头部信息, 反序列化(json.loads)
        #   最后接收真实文件
        conn.send(head_info_len)  # 发送head_info的长度
        conn.send(head_info.encode('utf-8'))

        #   发送真是信息
        with open(filemesg, 'rb') as f:
            data = f.read()
            conn.sendall(data)

        print('发送成功')