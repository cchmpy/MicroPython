import network, espnow
from machine import I2S, Pin
# I2S和ESPNowd的配置参数
config = {'id': 0,                # I2S的id
          'rate':16000,           # I2S采样率 
          'bits':16,              # I2S采样位深
          'format': I2S.MONO,     # 单声道
          'sd':23,                # I2S串行数据引脚
          'ws':21,                # I2S字选择引脚
          'sck':22,               # I2S串行时钟引脚
          'mck':None,             # I2S主时钟引脚
          'packet_size':240}      # ESP-NOW数据包大小(不大于250) 
          
class WirelessAudio():
    def __init__(self,device='mic'):
        # 打开射频模块
        self.sta = network.WLAN(network.STA_IF)
        self.sta.active(True)
        self.sta.disconnect()                     # 断开可能的Wi-Fi连接（ESP8266）
        
        # 初始化ESP-NOW
        self.e = espnow.ESPNow()
        self.e.active(True)
                
        # 初始化I2S(麦克风或扬声器)
        mode = I2S.RX if device=='mic' else I2S.TX
        self.audio = I2S(config['id'],sck=config['sck'],ws=config['ws'],sd=config['sd'],
                         mode=mode, bits=config['bits'],format=config['format'],
                         rate=config['rate'], ibuf=config['packet_size']*4)
    
    def mic(self,mac):                            # 麦克风端方法：采集→发送，mac是扬声器端设备mac地址
        self.e.add_peer(mac)                      # 添加一个对端设备
        size = config['packet_size']
        buf = bytearray(size)                     # 麦克风音频缓冲区
        audio=self.audio; e=self.e                # 局部变量缓冲类实例变量 
        print('正在采集音频...')
        try:
            while True: 
                n = audio.readinto(buf)           # 从I2S读取音频数据 
                if n == size: 
                    try: e.send(mac, buf, False)  # 异步发送，降低延迟
                    except OSError: pass          # 忽略发送失败（偶尔的丢包是可以接受的）
        except KeyboardInterrupt: print("退出程序")
        finally:                                  # 清理资源 
            audio.deinit()
            e.active(False)
            self.sta.active(False)
    
    def spk(self):                                # 扬声器端方法：接收→播放 
        size = config['packet_size'] 
        audio=self.audio; e=self.e                # 局部变量缓冲类实例变量
        print("接收端已启动，等待音频数据...")
        try:
            while True: 
                _, msg = e.irecv()                # 接收ESP-NOW数据 
                if msg and len(msg) == size: 
                    audio.write(msg)              # 将接收到的音频数据写入I2S播放 
        except KeyboardInterrupt: print("退出程序")
        finally:                                  # 清理资源 
            audio.deinit()
            e.active(False)
            self.sta.active(False)

if __name__=='__main__':
    # config['id'] = 0                            # 在此进行设置I2S和ESPNow相关选项
    device = 'mic'                                # 分别在两个的ESP32上设置mic和spk
    if device=='mic': WirelessAudio(device='mic').mic(b'\xa8B\xe3\xaen\xf8')         # 麦克风端
    else:             WirelessAudio(device='spk').spk()                              # 扬声器端
