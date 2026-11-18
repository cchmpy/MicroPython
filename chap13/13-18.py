import websocket,myutils,gc,time    # 载入扩展功能的websocket模块：10-13.py
from camera import Camera, FrameSize, PixelFormat,GrabMode
from micropython import const
_DELAY_MS = const(5)                # poll轮询超时时间/摄像头连续采集图像时两帧间的延时
_BLOCKING = const(False)            # on_polled回调函数是否阻塞运行
start = i = 0                       # 拍摄起始时间、帧数

cam = Camera(                       # 定义摄像头对象
    frame_size=FrameSize.QVGA, 
    pixel_format=PixelFormat.JPEG,
    jpeg_quality=60, 
    grab_mode=GrabMode.WHEN_EMPTY) 

def on_polled(ws):                  # 定义回调函数 
    global cam,i,start,blocking
    if i==0: start=time.time()      # 开始计时 
    while True:
        if cam.frame_available():
            img = cam.capture()
            ws.write(img)
            cam.free_buffer() 
            i += 1
            if i%40==0: print('fps:',i/(time.time()-start))
        if _BLOCKING: time.sleep_ms(_DELAY_MS)
        else: break
       
wlan = myutils.connect_wifi()
server = websocket.WSServer()
server.static_page(html_file='webcamera.html')
server.on_polled = on_polled
server.run(host=wlan.ifconfig()[0], port=80, poll_timeout=_DELAY_MS,
           frame_type=websocket.FRAME_BIN, blocking_write=True)
