def config_query(wlan):                         # 参数查询
    # wlan是STA或AP模式的网络接口对象
    args = ['mac','ssid', 'hidden','security','key', 'channel','hostname',
        'max_clients','reconnects','txpower','protocol','pm']
    for x in args:
        try:
            print(x,':',wlan.config(x))
        except Exception as err:
            print(x,'Error: ',err)
            continue 

def config_setup(wlan,**kwargs):                # 参数设置
    # kwargs是不定长关键字参数，例如config_setup(ap,ssid='esp32',key='12345678',security=4)
    k = kwargs.keys()
    for x in k:
        try:
            if p := kwargs.get(x,None):
                if x=='mac': wlan.config(mac=p)
                elif x=='ssid': wlan.config(ssid=p)
                elif x=='hidden': wlan.config(hidden=p)
                elif x=='security': wlan.config(security=p)
                elif x=='key': wlan.config(key=p)
                elif x=='channel': wlan.config(channel=p)
                elif x=='hostname': wlan.config(hostname=p)
                elif x=='max_clients': wlan.config(max_clients=p)
                elif x=='reconnects': wlan.config(reconnects=p)
                elif x=='txpower': wlan.config(txpower=p)
                elif x=='protocol': wlan.config(protocol=p)
                elif x=='pm': wlan.config(pm=p)
                print('setup',x)
        except Exception as err:
            print(x,'Error: ',err)
            continue 
if __name__ == '__main__':
    import network
    ap = network.WLAN(network.AP_IF)                       # 创建AP接口对象
    ap.active(True)                                        # 激活AP接口
    config_setup(ap,ssid='ESP32_AP',key='12345678',        # 配置热点参数
                 security=network.WLAN.SEC_WPA_WPA2,
                 max_clients=5)    
    if ap.active():
        print(f"已启用热点:{ap.ifconfig()}")                # 检查AP模式是否激活
        print('---------------参数配置情况---------------')
        config_query(ap) 
    else: print("启用热点失败")
