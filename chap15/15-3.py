import track,framebuf,array
w=160; h=120                       # 图像宽高
buf =bytearray(b'\xFF'*(w*h))      # 定义图像缓冲区，白色背景
f = framebuf.FrameBuffer(buf,w,h,framebuf.GS8)
# 在缓冲区上绘图，建立黑色色块
f.poly(100,0,array.array('h',[0,0,20,0,-40,119,-60,119]), 0, True)
f.rect(20,100,23,10,1,True)
f.rect(70,108,23,8,1,True)

ti = track.TrackImage(w,h,buffer=None,copy=False)
ti.update_image(buf)
for b in ti.find_blobs(x_stride=2, y_stride=2, area_thr=50, pixels_thr=20, invert=False):
    print(f'x={b.x},y={b.y},w={b.w},h={b.h},cx={b.cx},cy={b.cy},pixels={b.pixels},area={b.area}')
print(ti.find_offset())
ti.deinit()
