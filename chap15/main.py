import track, websocket, dcmotor, jpeg, json, framebuf, time
from camera import Camera, PixelFormat, FrameSize,GrabMode
from gc import collect
from machine import reset
from myutils import connect_wifi
from network import hostname
from esp32 import NVS
from sys import print_exception

class Tracker:                                                  # 巡线类
    @staticmethod
    def _write_txt(ws,hint):                                    # 向客户端发送文本帧信息
        ws.ioctl(websocket.SET_FRAME_TYPE, websocket.FRAME_TXT) # 使用文本帧
        ws.write(hint)                                          # 发送到客户端
        ws.ioctl(websocket.SET_FRAME_TYPE, websocket.FRAME_BIN) # 恢复二进制帧（图像传输）
        
    def __init__(self,motor_pin=[13,12,15,14], imgbuf_copy=True, width=160, height=120,fb_count=1):
        self.buf = memoryview(bytearray(4096))                  # 缓冲，用于读取浏览器发送的文件\读取NVS
        # NVS用于存储base_duty/p_value/threshold
        self.nvs = NVS('track')                                 # 创建命名空间为track的NVS对象

        # 电机
        self.motor=dcmotor.DCMotor(motor_pin,freq=50)           # 电机驱动对象
        self.base_duty=self._param_in_nvs('base_duty')          # 读取NVS中电机基础功率(功率范围0-100)
        self.p_value = self._param_in_nvs('p_value')            # 读取NVS中PID整定参数，仅使用p
        self.accelerate = self._param_in_nvs('accelerate')      # 读取NVS中直线加速递增比率
        self.motor.drive(0, 0)                                  # 机器人初始停止不动
        self.lduty =0; self.rduty =0                            # 左右电机功率 
        
        # 摄像头，双缓冲提高ESP32帧率,但ESP32-S3效果不大（可忽略执行时的警告信息）
        self.cam = Camera(frame_size=FrameSize.QQVGA, pixel_format=PixelFormat.GRAYSCALE,
                          grab_mode=GrabMode.WHEN_EMPTY, fb_count=fb_count) 
        self.cam.free_buffer()
        self.w = width; self.h = height                         # 图像宽度、高度
    
        # jpeg编码器
        self.encoder = jpeg.Encoder(pixel_format="GRAY", quality=65,
                                    rotation=0, width=width, height=height)
        
        # 定义巡线核心算法对象（寻找色块）
        self.tkimg = track.TrackImage(width, height, copy=imgbuf_copy) 
        self.threshold = self._param_in_nvs('threshold')        # 读取NVS中的灰度阈值
        self.weights=self._param_in_nvs('weights')              # 读取NVS中6个区域（从下到上）权重
        self.copy = imgbuf_copy                                 # 是否拷贝图像数据
        self.painter = None                                     # 绘图对象
        if imgbuf_copy: 
            self.painter = framebuf.FrameBuffer(self.tkimg.buffer(),width, height, framebuf.GS8)
        
        self.is_tracking = False                                # 是否正在巡线
        self.gc_trigger = 0                                     # 垃圾回收触发计数（1000帧执行一次）
        self.stop_trigger=0           # 停车触发计数，未发现道路则计数1次，累计10次（10帧）就停车        
    
    def _param_in_nvs(self,key,value=None):                     # 读取或设置NVS中的key参数值
        if value:                                               # 设置
            if key== 'weights': self.nvs.set_blob('weights',value.encode()) # value：类似'1,2,3,4,5,6'的字符串 
            else:               self.nvs.set_i32(key, value) 
            self.nvs.commit()
        else:                                                   # 读取
            try:
                if key=='weights':
                    size = self.nvs.get_blob(key, self.buf)
                    value = bytes(self.buf[:size]).decode()
                    value=[int(num) for num in value.split(',')]# 字符串转为整数列表
                else:
                    value = self.nvs.get_i32(key) 
            except OSError:                                     # 键不存在
                if key=='base_duty':     value=30               # 默认基准功率
                elif key=='p_value':     value=70               # 默认p值(扩大100倍的整数)
                elif key=='threshold':   value=80               # 默认阈值
                elif key=='accelerate':  value=5                # 4色块以上，每增加1个色块，速度增加该幅度
                elif key=='weights':     value='10,5,5,2,1,1'   # 默认ROI0-ROI5区域权重
                else: raise ValueError(f'没有键{key}')
                
                if key== 'weights': 
                    self.nvs.set_blob('weights',value.encode()) # 创建键值(bytes)对
                    value=[int(num) for num in value.split(',')]
                else: 
                    self.nvs.set_i32(key, value)                # 创建键值(整数)对                                        
                self.nvs.commit() 
            return value
        
    def camera_flip(self,horizontal=False, vertical=False):    # 翻转摄像头画面（ov5640可能需水平反转）
        if horizontal: self.cam.hmirror=True                   # 水平翻转
        if vertical: self.cam.vflip = True                     # 垂直翻转
    
    def on_connect(self,ws):                                   # 当客户端建立WebSocket连接时调用
        # 发送参数的初始值(json格式）
        paras = json.dumps({'base_duty':self.base_duty, 'p_value':round(self.p_value/100,2),
                            'threshold':self.threshold,'accelerate':self.accelerate,
                            'weights':','.join(map(str, self.weights))}) 
        Tracker._write_txt(ws,paras) 
    
    def on_recv(self,ws):                                      # 当收到客户端数据时调用
        data = ws.readline()                                   # 按行读取json数据
        if not data: return False                              # 无数据，客户端主动断连，返回False
        data = data.decode().strip()                           # 转为字符串，去除首尾空白
        try: 
            data = json.loads(data)                            # 解析JSON为字典对象
            if v:=data.get('cmd',None):                        # 收到指令
                d = self.base_duty                             # 缓存基准功率，用于控制电机转动
                if v=='start':
                    collect(); self.gc_trigger=0               # 巡线前垃圾回收
                    self.is_tracking = True                    # 开始巡线
                elif v=='stop':                                # 停止巡线
                    self.is_tracking = False
                    self.motor.drive(0, 0)
                elif v=='forward': self.motor.drive(d, d)      # 手动驾驶：前进                    
                elif v=='backward': self.motor.drive(-d, -d)   # 手动驾驶：后退
                elif v=='left': self.motor.drive(-d, d)        # 手动驾驶：原地左转
                elif v=='right':self.motor.drive(d, -d)        # 手动驾驶：原地右转
                elif v=='pause': self.motor.drive(0, 0)        # 手动驾驶：停止
                elif v=='reset':                               # 重置系统
                    ws.close()                                 # 关闭客户端（让客户端知道已关闭）
                    reset()                                    # 重置系统
            elif v:=data.get('base_duty',None):                # 收到参数设置
                self.base_duty = v
                self._param_in_nvs('base_duty',v) 
            elif v:=data.get('p_value',None):
                self.p_value = int(v*100)                      # 扩大100，使用整数
                self._param_in_nvs('p_value',self.p_value) 
            elif v:=data.get('threshold',None):
                self.threshold = v
                self._param_in_nvs('threshold',v) 
            elif v:=data.get('accelerate',None):
                self.accelerate = v
                self._param_in_nvs('accelerate',v)
            elif v:=data.get('weights',None):
                weights = [int(num) for num in v.split(',')]   # 字符串转为整数列表
                if len(weights) != 6: raise ValueError('权重数据的长度或格式(英文逗号)错误。')
                self.weights=weights 
                self._param_in_nvs('weights',v) 
            elif filename:=data.get('file',None):              # 收到文件(main.py/index.html)更新请求                
                f_size = data['size']                          # 文件总字节 
                try:
                    with open(filename,'w') as f:
                        sum_size = 0                           # 已读总字节数
                        while sum_size<f_size:                 # 可能需要多次读取
                            size = ws.readinto(self.buf)       # 每次最多4Kib
                            if size:                           # size可能是None或0
                                f.write(self.buf[:size])
                                sum_size += size 
                    hint = json.dumps({'hint':f'服务器已接收{filename},共{sum_size}字节。'})                    
                except Exception as e:
                    hint = json.dumps({'hint':f'接收文件{filename}出现错误:{e}'}) 
                Tracker._write_txt(ws,hint)                    # 发送提示信息
        except ValueError as e:
            hint = json.dumps({'hint':f'服务器无法解析JSON字段:{e}'})
            while size:=ws.readinto(self.buf): pass            # 读完所有无效数据
            Tracker._write_txt(ws,hint)  
        return True                                            # 返回True,告诉服务器收到数据

    def on_polled(self, ws):                                   # 轮询间隙的回调函数
        try:
            if not self.cam.frame_available(): return          # 帧缓冲是否可用
            img = self.cam.capture()
            self.tkimg.update_image(img)                       # 更新巡线所用图像
            if self.copy: self.cam.free_buffer()               # 释放摄像头帧缓存(提早释放，利于提高帧率)
            blobs = self.tkimg.find_blobs(threshold=self.threshold, x_stride=5,y_stride=5, area_thr=50,
                                          pixels_thr=30,invert=False) 
        
            if self.is_tracking:                               # 正在巡线 
                blobs_cnt = len(blobs)                         # 发现色块数量（几个区域有色块）                
                if blobs_cnt>0:
                    # 1、计算赛道与图像中心的加权像素偏移量
                    centre = self.w//2                         # 图像中心 
                    sum_w = sum_wdx = 0                        # 权重、权重偏移量之和
                    for b in blobs:                            # 计算权重和权重偏移量之和
                        w = self.weights[b.region_id]          # 该色块的权重
                        sum_w += w;                            # 权重之和 
                        if b.region_id == blobs_cnt-1:         # 特殊处理：计算最上方ROI的权重偏移量                            
                            if b.cx<centre:                    # 色块中心位于图像左边
                                sum_wdx += w * (b.x-centre)    # 使用色块左侧x坐标（非中心点）计算权重偏移量之和
                            else:                              # 色块中心位于图像右边
                                sum_wdx += w * (b.x+b.w-centre)# 使用色块右侧x坐标（非中心点）计算权重偏移量之和
                        else: sum_wdx += w * (b.cx-centre);    # 计算其他ROI的权重偏移量之和
                    dx = 0                                     # 偏移量初始值
                    if sum_w: dx = sum_wdx // sum_w            # 计算像素偏移量
                     
                    # 2、计算左右电机功率
                    duty = self.base_duty; p = self.p_value    # 基准功率和基准P值
                    if blobs_cnt>4:                            # 至少4个区域发现道路,道路较直,加速且降低P值
                        duty=self.base_duty+(blobs_cnt-4)*self.accelerate # 基准功率增加
                        p = p-(blobs_cnt-4)*p//5               # 减小p值（ESP32:5  ESP32-S3:4)
                    offset = dx*p//100
                    self.lduty=max(-100,min(100,duty+offset))  # 钳定数值
                    self.rduty=max(-100,min(100,duty-offset))  # 钳定数值 
                    # 3、当前帧巡线
                    self.motor.drive(self.lduty, self.rduty)   # 当前帧巡线
                else:                                          # 没有发现色块
                    self.stop_trigger += 1                     # 停车计数器累加
                    if self.stop_trigger>10:                   # 连续10次没发现道路
                        self.lduty=self.rduty=0;
                        self.stop_trigger=0                    # 停车计数器归零
                        
            if self.copy:                                      # 图像已拷贝 
                for b in blobs:                                # 遍历所有色块  
                    self.painter.rect(b.x,b.y,b.w,b.h,255,0)   # 绘制色块外围矩形框
                    self.painter.hline(b.cx-3,b.cy,7,255)      # 绘制色块中心十字
                    self.painter.vline(b.cx,b.cy-3,7,255)                 
                #for i in range(6): self.painter.rect(0,(5-i)*20,160,20,236) # 绘制roi区域矩形框
            else:
                self.cam.free_buffer() 
            
            ws.write(self.encoder.encode(self.tkimg.buffer())) # 发送图像 
            self.gc_trigger +=1
            if self.gc_trigger>=1000:
                collect(); self.gc_trigger=0                   # 垃圾回收
        except Exception as e:
            hint = json.dumps({'hint':f'巡线过程中出现错误:{e}'}) 
            Tracker._write_txt(ws,hint) 
           
    def deinit(self): 
        self.motor.drive(0, 0)
        self.motor.deinit()
        self.tkimg.deinit()
    
if __name__=='__main__':
    from os import uname
    if 'S3' in uname().machine:                            # ESP32-S3
        tk = Tracker(motor_pin=[42,41,2,1,], imgbuf_copy=True,width=160,height=120,fb_count=2) 
    else:                                                       # ESP32
        tk = Tracker(motor_pin=[13,12,15,14,], imgbuf_copy=True,width=160,height=120,fb_count=2) 
        tk.camera_flip(horizontal=True)                         # ov5640 摄像头需要左右翻转
    name = 'trackline'; hostname(name)                          # 设置主机名 
    wlan = connect_wifi()                                       # 连接互联网
    server = websocket.WSServer(max_ws_clients=1)               # 定义WebSocket服务器,最多1个客户端
    server.static_page(html_file='index.html')                  # 载入主页
    server.on_connect = tk.on_connect                           # 设置回调，WebSocket连接时调用
    server.on_recv = tk.on_recv                                 # 设置回调，收到客户端数据时调用
    server.on_polled = tk.on_polled                             # 设置回调，poll轮询间隙调用
    # 启动服务器：WebSocket默认二进制帧格式、写阻塞（确保完整发送数据）
    server.run(host=f'{name}.local', port=80, poll_timeout=5,
               frame_type=websocket.FRAME_BIN, blocking_write=True)
    tk.deinit()
