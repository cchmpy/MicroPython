import json, io, machine
stu = {'name':'Lili', 'grades':(95,80,86)}

# 序列化
jstr  = json.dumps(stu)                      # 解析为JSON字符串
jstr1 = json.dumps(stu,separators=(',',':')) # 解析为紧凑JSON字符串
print(jstr)                                  # 输出: {"name": "Lili", "grades": [95, 80, 86]}
print(jstr1)                                 # 输出: {"name":"Lili","grades":[95,80,86]}
buf = io.StringIO()                          # 字符流
# buf = io.BytesIO()                         # 字节流
# buf = open('1.json','w+')                  # 文件流
# buf = machine.UART(2)                      # UART流，若使用UART, 解析是需要先接收
json.dump(stu,buf,separators=(',',':'))      # 解析到流buf中
buf.flush()                                  # 更新底层缓冲

# 反序列化，模拟收到数据或打开JSON文件
buf.seek(0)                           # 从流开始位置读取数据
print(json.load(buf))                 # 解析流,         输出:{'name': 'Lili', 'grades': [95, 80, 86]}
print(json.loads(jstr1))              # 解析JSON字符串,输出:{'name': 'Lili', 'grades': [95, 80, 86]} 
buf.close()
