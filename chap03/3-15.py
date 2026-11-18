class LED:
    _count = 0  # 类级计数器
    @classmethod
    def get_instance_count(cls):
        return cls._count
    def __init__(self, pin):
        self.pin = pin
        self.__class__._count += 1           # 更新类变量
led1, led2 = LED(pin=12), LED(pin=13)        # 创建实例并统计数量
print(LED.get_instance_count())              # 输出: 2
