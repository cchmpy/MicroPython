import binascii
# 发送端代码
def send(data): pass                       # 模拟发送端，发送函数
data = bytearray(b'hello,MicroPython!')    # 数据包
crc = binascii.crc32(data)                 # 计算数据包CRC-32校验和 
data.extend(crc.to_bytes(4,'big'))         # 将CRC-32校验和添加到数据包末尾
send(data)                                 # 发送

# 接收端代码
def recv(): return data                    # 模拟接收端，接收函数
data = recv()                              # 接收
crc  = binascii.crc32(data[:-4])           # 计算数据包CRC-32校验和
if crc == int.from_bytes(data[-4:],'big'): # 进行校验
    print('CRC-32 OK!')
else:
    print('CRC-32 FAILED!')
