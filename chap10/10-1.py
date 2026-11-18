import network,time
# 配置STA模式（客户端，连接到现有Wi-Fi）
def connect_wifi(ssid='ssid',key='key',timeout=30):            # timeout是超时秒数
    sta = network.WLAN(network.STA_IF)                         # 创建STA接口对象
    sta.active(True)
    if not sta.isconnected():
        print(f'连接到{ssid}...')
        sta.connect(ssid, key)
        while not sta.isconnected() and timeout>0:             # 如果没有连接且不超时
            time.sleep(1); timeout -= 1 
    if sta.isconnected(): print(f"连接成功:{sta.ifconfig()}") 
    else: print("连接超时") 
    return sta

# 配置AP模式（热点，允许其它设备连接）
def create_ap(ssid='ESP32_AP',key='12345678',ip=None):
    ap = network.WLAN(network.AP_IF)                           # 创建AP接口对象
    ap.active(True)                                            # 激活AP接口
    if ip is not None:                                         # 设置网络层接口参数
        ap.ifconfig((ip, '255.255.255.0', ip, ip))
    ap.config(ssid=ssid, key=key, security=network.WLAN.SEC_WPA_WPA2)
    if ap.active(): print(f"已启用热点{ssid}:{ap.ifconfig()}")  # 检查AP接口是否激活
    else: print("启用热点失败")
    return ap

if __name__ == '__main__':                                     # 混合接口模式
    sta = connect_wifi(ssid='热点名称',key='密码')              # STA接口
    ap = create_ap()                                           # AP接口
    sta.disconnect(); ap.disconnect()                          # 断开连接