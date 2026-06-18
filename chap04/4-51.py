import network,machine
class WiFiManager:
    def __enter__(self):        
        self.wlan = network.WLAN()
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print('connecting to network...')
            self.wlan.connect('my_ssid', 'my_key') 
            while not self.wlan.isconnected():
                machine.idle()                         # 对CPU的时钟进行门控,降低功耗 
        return self    
    def __exit__(self, exc_type, exc_val, exc_tb):     # 默认返回None,若有异常继续抛出
        self.wlan.disconnect()
        self.wlan.active(False)

with WiFiManager () as wifi_conn:                      # connecting to network...
    print("已连接，IP:", wifi_conn.wlan.ifconfig()[0])  # 已连接，IP: 192.168.1.18
    ...                                                # 在此进行其他需要网络连接的工作
