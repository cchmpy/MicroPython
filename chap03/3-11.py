class TemperatureTooHighError(Exception):
    pass
def check_temperature(temp):
    if temp > 100:
        raise TemperatureTooHighError("温度超过安全阈值！")
try:
    check_temperature(105)
except TemperatureTooHighError as err:
    print(err)  # 输出: 温度超过安全阈值！
