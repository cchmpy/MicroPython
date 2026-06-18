import time 
class HardwareUtils:
    @staticmethod
    def calculate_checksum(data):  return sum(data) % 256      # 计算简单的校验和 
        
    @staticmethod
    def encode_for_uart(payload):                              # 为UART通信编码数据
        return bytes([0xAA, len(payload)]) + payload + \
               bytes([HardwareUtils.calculate_checksum(payload)])
    
    @staticmethod
    def delay_ms(ms): time.sleep_ms(ms)                        # 毫秒级延迟 

# 使用硬件工具方法
data = b"\x01\x02\x03"
encoded = HardwareUtils.encode_for_uart(data)
print(encoded)                                                 # 输出类似: b'\xaa\x03\x01\x02\x03\x06'
HardwareUtils.delay_ms(500)                                    # 延迟500毫秒
