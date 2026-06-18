import re, requests, myutils, socket
t_pattern = re.compile("温度:\s*(\d+\.?\d*)\s*°C")          # 编译搜索温度的正则表达式模式
h_pattern = re.compile("湿度:\s*(\d+\.?\d*)\s*%")            # 编译搜索湿度的正则表达式模式

myutils.connect_wifi()                                       # 连接wifi
ip_addr = socket.getaddrinfo('esp32-es.local',80)[0][-1][0]  # 解析ip地址
r = requests.get(f'http://{ip_addr}/')                       # 获取服务器内容
t_match = t_pattern.search(r.text)                           # 搜索温度
h_match = h_pattern.search(r.text)                           # 搜索湿度
r.close()
if t_match: print('温度:', t_match.group(1))
if h_match: print('湿度:', h_match.group(1))
