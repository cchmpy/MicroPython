import array,struct
from random import randint
with open('1.dat','wb') as f:                             # 数据生成
    cnt = 512                                             # 传感器采集数据的数量（2字节无符号整数）
    for i in range(0,cnt*2,2):
        f.write(randint(0,65535).to_bytes(2,'little'))    # 写入1个无符号整数

with open('1.dat', 'rb') as f1, open('2.dat','wb') as f2: 
    buf_size = 50
    buf = array.array('H',[0]*buf_size)                   # 定义缓冲区    
    while n := f1.readinto(buf):                          # 读取数据，最多buf_size*2字节
        for i in range(n//2):
            buf[i]= 0 if buf[i]<32767 else 65535          # 二值化处理        
        if n==buf_size*2: f2.write(buf)                   # 若缓冲内所有数据有效，则写入整个缓冲
        else: f2.write(buf[:n//2])                           # 缓冲内部分数据有效
    
    f1.seek(0)                                            # 定位到1.dat文件开头
    print(struct.unpack('<10H',f1.read(20)))              # 打印前10个数据（原始数据）                                                
    f2.seek(0)                                            # 定位到2.dat文件开头
    print(struct.unpack('<10H',f2.read(20)))              # 打印前10个数据（处理后的数据）

# 程序的输出可能如下：    
(31603, 2878, 46127, 64118, 29904, 8229, 55635, 51285, 56301, 16996)
(0, 0, 65535, 65535, 0, 0, 65535, 65535, 65535, 0)
