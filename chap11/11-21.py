import neopixel, json, time, gc
from machine import Pin
from myutils import connect_wifi
from websocket import WSServer       # 导入程序11-20.py（websocket.py）
# 硬件配置 
np = neopixel.NeoPixel(Pin(15), 1)                    # 定义驱动对象，根据实际连接修改WS2812的引脚 
rgb = bytearray(3)                                    # RGB灯的初始像素颜色(默认0,0,0)
np[0] = rgb;  np.write()                              # 写入颜色
# 保存不同客户端状态的字典：key是客户端ws对象，value是上次发送灯颜色的时间)
CLIENT_STATES = {}
def on_recv(ws):                                      # 定义回调函数:on_recv
    global  np, rgb
    data = ws.read()                                  # 读取数据
    if not data: return False                         # 没有读到数据，返回False(客户端主动断开)
    data = data.decode().strip()                      # 转为字符串，去除首尾空白
    try: 
        data = json.loads(data)                       # 解析JSON，控制灯的颜色
        rgb[0] = max(0, min(255, data['r']))
        rgb[1] = max(0, min(255, data['g']))
        rgb[2] = max(0, min(255, data['b']))
        np[0]=rgb;  np.write()                        # 调整灯的颜色
        print('控灯:', rgb[0], rgb[1], rgb[2]) 
    except ValueError: pass                           # 忽略json解析异常
    return True
        
def on_polled(ws):                                    # 定义用户回调函数:on_polled
    global CLIENT_STATES, rgb 
    if ws not in CLIENT_STATES:                       # 初始化当前客户端的独立状态（仅首次执行）
        CLIENT_STATES[ws] = time.ticks_ms()           # 独立定时
    now = time.ticks_ms()
    if time.ticks_diff(now, CLIENT_STATES[ws]) >= 1000: 
        status = json.dumps({'r':rgb[0], 'g':rgb[1], 'b':rgb[2]})
        ws.write(status)                              # 上报当前颜色
        CLIENT_STATES[ws] = now                       # 更新当前客户端的计时状态
        gc.collect()                                  # 垃圾回收 
    
wlan = connect_wifi() 
server = WSServer()
server.static_page(html_file='ws2812_index.html')     # 注册网页（使用文件）
server.on_recv = on_recv                              # 注册on_recv回调
server.on_polled = on_polled                          # 注册on_polled回调 
server.run(host=wlan.ifconfig()[0], port=80, blocking_write=False) # 启动服务器
