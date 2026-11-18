import miniui as ui, gc, time, sys
from machine import I2C, SPI, PWM
from st77xx import ST77xx as ST
from ft6336u import FT6336U as FT
# 显示模块带字库芯片。若无字库芯片，用font_file，需修改font对象和字号的定义。
from font_flash import Font 
# 根据开发板和屏幕分辨率，修改引脚和宽高------------------------------------------
board = sys.implementation._machine
if 'ESP32-S3' in board:
    leds = [PWM(16,freq=1000,duty=0), PWM(17,freq=1000,duty=0), PWM(18,freq=1000,duty=0)]
    i2c=I2C(0,scl=15,sda=38)
    ft=FT(i2c,rst=40,irq=47)
    w = 320; h = 480
    spi = SPI(1,baudrate=40_000_000, sck=12, mosi=11, miso=13)
    font = Font(spi,39)    
    lcd=ST(spi,dc=9,cs=10,rst=14,bl=4,width=w,height=h,font=font,
               source_forward=False, clr_inverse=True)
elif 'ESP32' in board:
    # PWM控制3个LED灯，模拟亮度可调照明灯
    leds = [PWM(25,freq=1000,duty=0), PWM(26,freq=1000,duty=0), PWM(27,freq=1000,duty=0)]
    # 触摸屏
    i2c=I2C(0,scl=13,sda=12) 
    ft=FT(i2c,rst=None,irq=14)    
    # 液晶屏和字库
    w = 240; h = 320                       # 液晶屏分辨率  
    spi = SPI(2, 20_000_000, sck=0, mosi=4, miso=5)
    font = Font(spi,22)                    # font = Font('font_12_map_dir.bin')
    lcd=ST(spi,dc=19,cs=21,rst=18,bl=23,width=w,height=h,font=font,
               source_forward=True, clr_inverse=False )


# 以下代码对于ESP32和ESP32-S3都相同，无需修改------------------------------------------
if ft.power_mode()!=ft.P_ACTIVE:           # 处理非主动电源模式(长时间无操作,进入休眠状态)
        ft.power_mode(ft.P_ACTIVE)

# 三个LED对应控件
buttons = [None,None,None]                 # 三个按钮
labels  = [None,None,None]                 # 三个标签，提示亮度（如：客厅 100）
sliders = [None,None,None]                 # 三个滑块
texts   = ('客厅','卧室','厨房')            # 按钮、标签使用的文本

# 根据屏幕宽度，定义控件的大小、字号、间距等数据(控件布局)
if w==240:
    img_w = img_h = 64
    font_h=16
elif w==320:
    img_w = img_h = 96
    font_h=24
else: raise ValueError('')                 # 其他分辨率，需生成适配的图片
btn_w = img_w                              # 按钮宽
btn_h = img_h+font_h+4                     # 按钮高

h_space = (w-3*img_w)//4                   # 水平排列控件间的像素间隔（最多水平排列三个按钮）
sld_w = w-2*h_space                        # 滑块宽
sld_h = int(0.08*h)                        # 滑块高
v_space = (h-btn_h-3*(font_h+4+sld_h))//5  # 垂直排列控件间的像素间隔（标签和滑块组合在一起，垂直间隔4像素）

ctl_bg_clr = ST.rgb565(80,80,80)           # 控件背景色
lcd_bg_clr = ST.rgb565(30,30,30)           # 屏幕背景
focus_clr = ST.rgb565(120,120,90)          # 控件有焦点时的颜色
font_clr = ST.GREY                         # 字体颜色

# 根据屏幕像素宽，载入两个图像文件（熄灯、开灯状态）
with open(f'bulb_off_{img_w}x{img_h}.ebm','rb') as f0, \
     open(f'bulb_on_{img_w}x{img_h}.ebm','rb') as f1:
    imgs = (f0.read(),f1.read())           # 熄灯、开灯图像

# 控件管理器
manager = ui.ControlManager(lcd=lcd, touch=ft,  font=font)

# 三个水平排列的按钮控件
def btn_press_cb(btn):                        # 按键回调函数(开关灯)
    i = texts.index(btn.text)                 # 哪个灯    
    d = not bool(leds[i].duty())              # 获取当前功率并转为布尔值(新状态）
    if d: leds[i].duty(1023)                  # 点亮
    else: leds[i].duty(0)                     # 熄灭
    buttons[i].set_image(img_data=imgs[d])    # 设置新状态图像
    labels[i].update_text(text=f'{texts[i]} {d*100}')     # 更新图标显示的功率
    sliders[i].update_value(value=d*100)      # 更新滑块
    
for i in range(3):
    buttons[i] = ui.Button(manager, h_space+i*(btn_w+h_space),v_space,btn_w, btn_h,
                    text=texts[i], img_w=img_w, img_h=img_h, img_data=imgs[0],
                    normal_clr=ctl_bg_clr, pressed_clr=focus_clr, font_h=font_h,
                    press_cb=btn_press_cb)
    manager.add_control(buttons[i])

# 三个垂直排列的标签和滑块
sliders_id =[0,0,0]                                   # 保存三个滑块的ID，用于识别滑块
def on_change(slider):                                # 滑块回调函数（改变亮度触发）
    i = sliders_id.index(slider.id)                   # 第几个滑块
    v = sliders[i].value                              # 滑块当前值
    d = v*1023//100                                   # 要设置的功率
    cur_d = leds[i].duty()                            # 当前功率
    if d == cur_d: return                             # 无需设置
    leds[i].duty(d)                                   # 设置功率
    labels[i].update_text(text=f'{texts[i]} {v}')     # 更新图标显示的功率
    if bool(d) != bool(cur_d):        
        buttons[i].set_image(img_data=imgs[bool(d)])  # 更改按钮图片
        buttons[i].draw(canvas=ui.CANVAS_LCD)         # 更新液晶屏图像

for i in range(3):
    y =btn_h+(i+2)*v_space + i*(font_h+sld_h+4)       # 标签的y坐标
    labels[i] = ui.Label(manager, h_space, y,font_h*5,30,text=f'{texts[i]} 0',
                     bg_clr=lcd_bg_clr, font_clr=font_clr, font_h=font_h)
    sliders[i] = ui.Slider(manager, h_space, y+font_h+4, sld_w, sld_h,
                value=0, bg_clr=lcd_bg_clr, on_change=on_change)
    manager.add_control(labels[i], sliders[i])
    sliders_id[i] = sliders[i].id                     # 保存Slider控件的id
    
# 填充液晶屏背景，显示所有控件-----------------------------------------------
lcd.fill(lcd_bg_clr)
manager.draw_all(ui.CANVAS_FRAME)
lcd.show()
try:           
    while True:
        time.sleep(1)
        gc.collect()
except KeyboardInterrupt:
    lcd.deinit()
    spi.deinit()
    for led in leds:
        led.deinit()
    sys.exit(0)
