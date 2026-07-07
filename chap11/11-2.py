import network,time
# 配置STA模式（客户端，连接到现有Wi-Fi）
def connect_wifi(ssid='热点名称',key='密码',timeout=30,ip=None): # timeout是超时秒数
    sta = network.WLAN(network.STA_IF)                         # 创建STA接口对象
    sta.active(True)                                           # 激活STA模式
    if ip is not None:                                         # 设置ip
        ips = ip.rsplit('.',1)                                 # ip地址拆分为2部分
        if ips[0]=='192.168.1' and 1<int(ips[1])<255:
            sta.ifconfig((ip, '255.255.255.0', '192.168.1.1', '192.168.1.1'))
    if not sta.isconnected():
        print(f'连接到{ssid}...')
        sta.connect(ssid, key)
        while not sta.isconnected() and timeout>0:             # 如果没有连接且不超时
            time.sleep(1)
            timeout -= 1 
    if sta.isconnected(): print(f"连接成功:{sta.ifconfig()}") 
    else: print("连接超时") 
    return sta 

# 配置AP模式（热点，允许其它设备连接）
def create_ap(ssid='ESP32_AP',key='12345678',ip=None):
    ap = network.WLAN(network.AP_IF)                           # 创建AP接口对象
    ap.active(True)                                            # 激活AP接口
    if ip is not None:                                         # 设置IP
        ips = ip.rsplit('.',2)                                 # ip地址拆分为3部分
        if ips[0]=='192.168' and ips[1]!='1' and 0<int(ips[2])<255:
            ap.ifconfig((ip, '255.255.255.0', ip, ip))
    # 配置热点参数
    ap.config(ssid=ssid, key=key, security=network.WLAN.SEC_WPA_WPA2)
    if ap.active(): print(f"已启用热点{ssid}:{ap.ifconfig()}")  # 检查AP模式是否激活
    else: print("启用热点失败")
    return ap 

if __name__ == '__main__':
    sta = connect_wifi()                                       # STA模式的网络接口
    ap = create_ap()                                           # AP模式的网络接口
