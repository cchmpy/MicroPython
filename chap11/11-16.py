import requests,myutils
myutils.connect_wifi()                                 # 连接Wi-Fi

def request(url,method='GET',**kw):
    r = requests.request(method,url,**kw)              # 客户端发出请求并获得响应
    print('code:',r.status_code)                       # 响应状态码,如200
    print('reason:',r.reason)                          # 响应状态码对应文本,如'OK'
    print('headers:',r.headers)                        # 响应头字典
    print('context:',r.content[:64])                   # 响应体字节数据
    print('text:',r.text[:64])                         # 响应体字符串数据
    try:    
        print('json:',r.json())                        # 响应体中json数据
    except ValueError: pass
    print('\n')
    r.close()                                          # 关闭与服务区的socket连接

url = 'http://192.168.1.23'                            # 设备监控HTTP服务器（已经启动服务）
request(url,'GET')                                     # 主页请求
request(f'{url}/update')                               # 更新设备信息请求
request(f'{url}/set/bright','POST',json={'brig':78})   # 设置亮度
request(f'{url}/submit', 'POST',data='brig=78&d=led',  # 无效路径(表单提交)
        headers={'Content-Type':'application/x-www-form-urlencoded'})
