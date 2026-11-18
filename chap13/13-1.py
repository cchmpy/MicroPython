from machine import ADC
class LM35CZ:
    def __init__(self, pin, atten=ADC.ATTN_0DB):
        self._adc = ADC(pin, atten=atten)         # ADC默认无衰减 
    def read(self):
        return round(self._adc.read_uv()/10000,1) # 结果保留1位小数
    def read_raw(self):
        return self._adc.read_uv()                # 返回原始值

if __name__ == '__main__':
    import time
    lm35 = LM35CZ(32)             # LM35DZ的输出引脚接ESP32的32引脚
    t = 0
    for i in range(10):
        t += lm35.read_raw()
        time.sleep_ms(25)
    print(f'LM35: {t/100000:.1f}')
