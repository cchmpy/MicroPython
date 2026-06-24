from machine import SoftSPI,Pin
spi = SoftSPI(baudrate=100000,sck=0, mosi=2, miso=4)
spi.init(baudrate=200000)           # 设置波特率
cs1 = Pin(23, Pin.OUT, value=1)     # 指定片选控制引脚，它与外围从设备1的cs引脚连接
cs2 = Pin(22, Pin.OUT, value=1)     # 指定片选控制引脚，它与外围从设备2的cs引脚连接

cs1(0)                              # 激活设备1，ESP32与设备1通信
spi.write(b'\xA5')                  # 写入一个从设备支持的寄存器指令
spi.read(10)                        # 从MISO上读取10字节
spi.read(10, 0xff)                  # 从MISO上读取10字节的同时，在MOSI上连续输出0xff
buf = bytearray(50)  
spi.readinto(buf)                   # 读取50字节的数据到缓冲区buf
spi.readinto(buf, 0xff)             # 读取50字节到buf的同时，在MOSI上连续输出0xff
cs1(1)                              # 关闭与设备1的通信

cs2(0)                              # 激活设备2，ESP32与设备2通信
spi.write(b'12345')                 # 在MOSI上写入5个字节的数据
buf = bytearray(4)
spi.write_readinto(b'1234', buf)    # 将数据b'1234'写入MOSI，并从MISO读取数据到缓冲区buf
spi.write_readinto(buf, buf)        # 将buf写入MOSI，并将MISO读回buf
cs2(1)                              # 关闭与设备2的通信
spi.deinit()                        # 关闭SPI总线