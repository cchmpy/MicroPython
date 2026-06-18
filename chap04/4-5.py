from machine import ADC, Pin
def read_sensor_average(sensor_pin, samples=3):    
    adc = ADC(sensor_pin)
    def _read_once():                                 # 嵌套函数：单次读取传感器（隐藏实现细节）
        value = adc.read_u16()
        ...                                           # 此处对value进行处理或添加其他逻辑
        return  value
    total = sum(_read_once() for _ in range(samples)) # 计算多次采样之和
    return total // samples                           # 计算多次采样的平均值
avg = read_sensor_average(Pin(26))                    # 读取模拟传感器（引脚26）的平均值
print(avg)
