from st77xx import FrameBufferRGB, ST77xx as ST
from ft6336u import TPoint, FT6336U as FT
from micropython import schedule, const
import time, gc
CANVAS_FRAME = const(0)                              # 把控件绘制在lcd（ST77xx）的帧缓冲上
CANVAS_LCD   = const(1)                              # 把控件绘制在lcd屏幕上
CANVAS_BOTH  = const(2)                              # 把控件同时绘制在lcd的帧缓冲和屏幕上

class ControlManager:                                # 控件管理器
    def __init__(self, lcd, touch, font):
        # 注入核心硬件实例（解耦、无需全局变量、仅传递一次、可扩展）
        self.lcd = lcd                               # 液晶屏对象
        self.touch = touch                           # 触摸屏对象
        self.font = font                             # 字库对象
        self.active_ctl = []                         # 存储交互控件（Button/Slider等）
        self.passive_ctl = []                        # 存储非交互控件（Label/Image等）
        self.touch.period_active(25)                 # 设置触屏Active模式下的报点周期(ms)（可选步骤）
        self.touch.set_callback(self._touch_callback)# 设置触屏回调
        self.id = 0                                  # 待添加控件的唯一标识码  
        
    def _handle_all(self,tp):                        # 把触点信息分发给所有交互控件处理
        for c in self.active_ctl: c.handle_touch(tp) # 控件基类拥有handle_touch()方法
        
    def _touch_callback(self, _):                    # 触摸回调：统一处理触摸事件 
        tp = self.touch.get_touch(1)                 # 读取触点1信息（当前方案不支持2点触控）
        # 如果需要判断手势（如左滑、右滑），可取消下方注释
#         if tp.event == self.touch.E_LIFT_UP:         # 手指抬起 
#             tp.gest = self.touch.get_slide_direc()   # 获取手势（滑动方向）
#         elif tp.event == self.touch.E_PRESS_DOWN:    # 手指按下
#             self.touch.set_slide_start()             # 设置滑动起点（用于计算手势）
        try: schedule(self._handle_all, tp)          # 使用调度函数处理一个可能比较耗时的操作
        except RuntimeError as e: pass               # 忽略调度处理过程中的异常，如调度队列已满
    
    def add_control(self, *control):                 # 添加一或多个控件到管理器 
        for ctl in control:                          # 根据is_interactive属性添加到不同列表
            ctl.id = self.id                         # 为控件id编码
            self.id += 1                             # 下一个控件的id
            if ctl.is_interactive: self.active_ctl.append(ctl)
            else:                  self.passive_ctl.append(ctl)
        
    def draw_all(self, canvas=CANVAS_FRAME):         # 在指定画布上统一绘制所有控件
        for ctl in self.passive_ctl:ctl.draw(canvas) # 非交互控件
        for ctl in self.active_ctl: ctl.draw(canvas) # 交互控件

class BaseControl:                                   # 控件基类
    def __init__(self, manager, x, y, w, h):         # manager:控件管理器对象
        self.lcd   = manager.lcd                     # 缓存manager的硬件对象，方便引用
        self.touch = manager.touch
        self.font  = manager.font
        self.id    = None                            # 控件唯一标识，由管理器自动赋值
        self.x=x; self.y=y; self.w=w; self.h=h       # 控件矩形区域
        self.is_interactive = False                  # 是否为交互控件
        # 触摸状态
        self.start_pt = 0                            # 保存“按下”事件的开始时间
        self.last_ct  = 0                            # 保存上次“接触”事件的时间
        self.tp = TPoint()                           # 上次触点对象
        self.focus = False                           # 是否通过“按下”事件获得焦点,用于控制绘图
        # 防抖/阈值参数（可被子类覆盖）
        self.DEBOUNCE_THD = 50                       # 防抖阈值（ms）
        self.LONG_PRESS_THD = 1000                   # 长按阈值（ms）
            
    def is_in_area(self, x, y):                      # 交互逻辑：判断坐标是否在控件区域内
        return (self.x<=x<self.x+self.w) and (self.y<=y<self.y+self.h)
   
    def handle_touch(self, tp):                      # 交互逻辑:基础触摸事件处理（子类可重写扩展）
        if not self.is_in_area(tp.x,tp.y):           # 不是触摸该控件
            if self.tp.event==FT.E_CONTACT:          # 该控件上次是滑动离开，需处理视觉反馈
                self.tp.event = FT.E_NO_EVENT        # 手动重置上次事件
                self.focus = False                   # 失去焦点
                self.draw(CANVAS_LCD)                # 根据事件，重新绘制视觉反馈
            return 
        cur_time = time.ticks_ms()                   # 当前时间
        if tp.event==FT.E_CONTACT and self.focus:    # 接触事件（如滑动、拖动）
            diff=time.ticks_diff(cur_time,self.last_ct)   # 计算时间差
            if diff>=self.DEBOUNCE_THD:              # 避免过快刷新
                self.last_ct = cur_time              # 更新last_ct
                self.tp.init(tp)                     # 更新上一个触点信息
                self.on_drag()                       # 触发拖动钩子
                self.draw(CANVAS_LCD)                # 立即在屏幕上重绘（视觉反馈）
        elif tp.event==FT.E_PRESS_DOWN:              # 按下事件
            self.focus=True                          # 获得焦点
            self.start_pt=self.last_ct=cur_time      # 记录起始时间，用于防抖等
            self.tp.init(tp)                         # 更新上一个触点信息
            self.on_press()                          # 触发按下钩子
            self.draw(CANVAS_LCD)                    # 立即在屏幕上重绘（视觉反馈）
        elif tp.event==FT.E_LIFT_UP and self.focus:  # 松开事件（防抖+触发释放钩子）
            self.focus=False
            diff=time.ticks_diff(cur_time,self.start_pt) # 计算时间差
            if diff>=self.DEBOUNCE_THD:              # 过滤抖动（短按<防抖阈值视为无效）
                self.tp.init(tp)                     # 更新上一个触点信息
                self.on_release()                    # 点触有效，触发释放钩子
            self.draw(CANVAS_LCD)                    # 立即在屏幕上重绘（视觉反馈）
    
    def on_press(self):  pass                        # 按下时触发（钩子方法，子类选择实现）
    def on_release(self):pass                        # 抬起时触发（钩子方法，子类选择实现）
    def on_drag(self):   pass                        # 拖动时触发（钩子方法，子类选择实现）
    def draw(self,canvas=CANVAS_LCD):                # 绘制方法  （抽象方法，子类必须实现）
        raise NotImplementedError('子类必须实现draw()方法')

    def _draw(self, canvas=CANVAS_LCD):              # 子类共用方法（将控件帧缓冲绘制到指定画布）
        if canvas==CANVAS_LCD:
            self.lcd.image_on_lcd(self.x,self.y,self.w,self.h,self.framebuf)
        elif canvas==CANVAS_FRAME:
            self.lcd.image(self.x,self.y,self.w,self.h,self.framebuf)
        elif canvas==CANVAS_BOTH:
            self.lcd.image(self.x,self.y,self.w,self.h,self.framebuf)
            self.lcd.image_on_lcd(self.x,self.y,self.w,self.h,self.framebuf)
    
    def _load_rgb565(self, img_path):                # 从Flash/SD卡加载RGB565格式的图像文件 
        try:
            with open(img_path, 'rb') as f: return f.read() 
        except Exception as e: return None           # 出错直接返回None

class Label(BaseControl):                                   # 文本标签类 
    def __init__(self, manager, x, y, w, h, text='',bg_clr=ST.WHITE,
                 font_clr=ST.BLACK, font_h=12, line_spacing=4): 
        super().__init__(manager, x, y, w, h)
        self.framebuf=FrameBufferRGB(w,h,self.font)         # 绘制文本的帧缓冲
        self.is_interactive = False                         # 非交互控件
        self.text = text                                    # 文本
        self.font_clr = font_clr                            # 文本颜色
        self.font_h = font_h                                # 字高
        self.bg_clr = bg_clr                                # 背景色
        self.line_spacing = line_spacing                    # 行间距

    def handle_touch(self,tp): return                       # 屏蔽所有交互逻辑
    def draw(self,canvas):
        self.framebuf.fill(self.bg_clr)                     # 填充背景色 
        if self.text:
            self.framebuf.text_gb2312(self.text, 0, 0, font_clr=self.font_clr,
                         font_h=self.font_h, alpha=True,line_spacing=self.line_spacing)
        self._draw(canvas) 
    # 更新文本属性
    def update_text(self,*, text='', font_clr=None, font_h=None, canvas=CANVAS_LCD): 
        if font_h: self.font_h = font_h                     # font_h不能为0
        if font_clr is not None: self.font_clr = font_clr   # font_clr可以是0
        self.text = text
        self.draw(canvas)                                   # 默认在屏幕上绘制

class Image(BaseControl):
    def __init__(self, manager, x, y, w, h, img_data=None, img_path=None):
        super().__init__(manager,x, y, w, h)               # w/h是图像的宽度和高度
        # RGB565图像数据（二选一），self.framebuf无法绘图
        self.framebuf =img_data if img_data else self._load_rgb565(img_path)
        self.is_interactive = False                        # 非交互控件 
        
    def handle_touch(self,tp): return                      # 屏蔽所有交互逻辑
    def draw(self, canvas):                                # 直接调用基类绘图函数
        if self.framebuf:  self._draw(canvas)
   
    def update_image(self, *, img_data=None, img_path=None, canvas=CANVAS_LCD):   # 在指定画布更新图像数据。
        # 优先使用img_data; 当img_path也为None时，_load_rgb565返回None
        self.framebuf = img_data if img_data else self._load_rgb565(img_path)
        self.draw(canvas); gc.collect()                    # 绘图、回收原图像数据（可选）
                
class Button(BaseControl):                                            # 子类：按钮控件
    def __init__(self, manager, x, y, w, h, text='', normal_clr=ST.GREY,
                 pressed_clr=ST.BLUE, font_clr=ST.WHITE, font_h=16,
                 img_w=None, img_h=None, img_data=None, img_path=None,
                 press_cb=None, long_press_cb=None):       
        super().__init__(manager,x, y, w, h)
        self.framebuf=FrameBufferRGB(w,h,self.font)                    # 绘制按钮的帧缓冲
        self.is_interactive = True                                     # 交互控件 
        # 背景颜色（正常和按下事件的视觉反馈）
        self.normal_clr=normal_clr; self.pressed_clr=pressed_clr
        # 文本属性（单行文本，不含换行符）
        self.text=text; self.font_clr=font_clr; self.font_h = font_h
        # 图像属性
        self.img_w=img_w; self.img_h=img_h
        self.set_image(img_data=img_data, img_path=img_path)
        # 用户定义回调
        self.press_cb = press_cb                                       # 短按回调
        self.long_press_cb = long_press_cb                             # 长按回调
    
    def set_image(self,*,img_data=None, img_path=None):                # 设置图像
        self.img_data=img_data if img_data else self._load_rgb565(img_path) 
    
    def on_release(self):                                              # 抬起事件回调 
        duration = time.ticks_diff(time.ticks_ms(),self.start_pt)
        if duration < self.LONG_PRESS_THD:                             # 执行短按回调 
            if self.press_cb: self.press_cb(self) 
        else: 
            if self.long_press_cb: self.long_press_cb(self)            # 执行长按回调
                
    def draw(self,canvas):                                             # 按钮绘制逻辑 
        if self.tp.event == FT.E_CONTACT: return                       # "接触"事件不绘制
        bg_clr = self.pressed_clr if self.focus else self.normal_clr   # 根据状态选择背景色
        self.framebuf.fill(bg_clr)                                     # 填充按钮背景
        
        if self.text:                                                  # 计算单行文本占用像素的宽高
            n = sum(1 for c in self.text if ord(c) < 128)              # ascii字符数量
            tw = (len(self.text)-n)*self.font_h + n*self.font_h//2     # 文本的像素宽度
            th = self.font_h                                           # 文本的像素高度
        else: tw = th = 0       
        tx = (self.w - tw) // 2                                        # 文本x坐标，中心对齐
        
        if self.img_data:                                              # 有图像，图像在上、文字在下
            img_x = (self.w - self.img_w) // 2                         # 图x坐标，水平居中
            img_y = (self.h-self.img_h-th-bool(th)*4)//2               # 图y坐标,垂直居中,图文间隔4像素
            self.framebuf.image(img_x, img_y, self.img_w,self.img_h,self.img_data)   # 绘图
            # 有焦点且图像至少在一个方向占满整个按钮，则绘制图像边框作为视觉反馈
            if self.focus and (self.img_w==self.w or self.img_h==self.h):
                self.framebuf.rect(img_x, img_y,self.img_w,self.img_h,self.pressed_clr,0)
            ty = img_y+self.img_h+4                                    # 文本y坐标,图文间隔4像素 
        else:  ty = (self.h - th) // 2                                 # 没有图像，文字在中心
        if tw: self.framebuf.text_gb2312(self.text, tx, ty, font_clr=self.font_clr,
                                         font_h=self.font_h, alpha=True) # 绘制文字
        self._draw(canvas)                                             # 把控件缓冲区图像绘制到canvas

class Slider(BaseControl):                                 # 滑动块控件    
    def __init__(self, manager, x, y, w, h, min_val=0, max_val=100, value=0,
                 bg_clr=ST.BLACK, track_bg_clr=ST.GREY, track_filled_clr=ST.RED, thumb_clr=ST.BLUE,
                 on_change=None, horizontal=True):
        super().__init__(manager, x, y, w, h)              # 初始化基类
        self.framebuf = FrameBufferRGB(w,h)                # 控件绘图缓冲区
        self.is_interactive = True                         # 交互控件
        # 滑块取值
        self.min_val=min_val; self.max_val=max_val;        # 滑动最大、最小值
        self.value=value                                   # 当前值
        self.range = max_val-min_val                       # 取值范围
        self.on_change = on_change                         # 值变化回调函数
        # 绘制颜色、样式 
        self.bg_clr       = bg_clr                         # 控件背景色（矩形容器）
        self.track_bg_clr = track_bg_clr                   # 滑动轨道背景色
        self.track_filled_clr = track_filled_clr           # 轨道填充色（有效值部分）        
        self.thumb_clr  = thumb_clr                        # 滑块按钮颜色
        self.horizontal = horizontal                       # True:水平滑块, False:垂直滑块
   
    def on_drag(self):                                     # 拖动回调方法
        t = abs(self.w-self.h)                             # 有效滑动的坐标区间
        # 计算当前坐标对应的滑块值v
        if self.horizontal: v = self.min_val+(self.tp.x-self.x-self.h//2)*self.range//t
        else:               v = self.min_val+(self.tp.y-self.y-self.w//2)*self.range//t
        v = max(self.min_val, min(self.max_val, v))        # 钳定取值范围 
        if self.value!=v:                                  # 值不变，无需调用回调
            self.value=v
            if self.on_change: self.on_change(self)        # 触发值变化回调，自动传递对象本身

    def on_press(self): self.on_drag()                     # “按下”事件回调方法
    
    def draw(self,canvas):                                 # 在控件缓冲区绘图并在canvas显示
        self.framebuf.fill(self.bg_clr)                    # 填充背景        
        if self.horizontal:                                # 水平滑块
            track_h = self.h//4                            # 轨道高度
            r = self.h//2                                  # 按钮半径（圆形）
            y = (self.h-track_h)//2                        # 轨道左侧y坐标
            filled_w = r+(self.value-self.min_val)*(self.w-self.h)//self.range    # 轨道填充宽度（有效值） 
            self.framebuf.rect(0, y, filled_w, track_h, self.track_filled_clr,1)  # 绘制填充轨道
            self.framebuf.rect(filled_w,y, self.w-filled_w, track_h,self.track_bg_clr,1) # 绘制剩余轨道
            self.framebuf.ellipse(filled_w,r,r,r,self.thumb_clr,1)                # 绘制滑块
        else:                                              # 垂直滑块
            track_w = self.w//4                            # 轨道宽度
            r = self.w//2
            x = (self.w-track_w)//2                        # 轨道上边x坐标
            filled_h = r+(self.value-self.min_val)*(self.h-self.w)//self.range      # 轨道填充高度            
            self.framebuf.rect(x, 0, track_w, filled_h, self.track_filled_clr,1) 
            self.framebuf.rect(x, filled_h, track_w, self.h-filled_h, self.track_bg_clr,1)
            self.framebuf.ellipse(r,filled_h,r,r,self.thumb_clr,1)            
        self._draw(canvas)                                 # 把控件缓冲区图像绘制到canvas
    
    def update_value(self, value, canvas=CANVAS_LCD):      # 更改当前值，并引发重绘
        if self.min_val<=value<=self.max_val:
            self.value = value
            self.draw(canvas)
        