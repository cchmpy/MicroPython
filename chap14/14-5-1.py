import time,tm1638                                     # 引用程序14-5.py（tm1638）
keys ='123+456-789*0.=/'                               # 键盘从上到下，从左到右的布局
seg=tm1638.TM1638(8,DIO=23,CLK=22,STB=21,comm_anode=True)
seg.show('0',bright=5,left_aligned=False,reverse=True) # 开机显示0 
a = [None,None,None,None]                              # [运算数1，运算数2，运算符，结果]
i = 0                                                  # 当前输入运算数的下标：a[i]
dot = 0                                                # 当前输入是小数点后第几位
def calculate():                                       # 计算: a[0] x a[1] = a[3],x=a[2]是运算符
    global  a,i,seg
    if a[0] is None or a[1] is None: return           # 缺少运算数
    if  a[2] =='+': a[3]=a[0]+a[1]
    elif a[2] =='-': a[3]=a[0]-a[1]
    elif a[2] =='*': a[3]=a[0]*a[1]
    elif a[2] =='/':
        if a[1]: a[3]=a[0]/a[1]
        else:
            seg.show('ERROR')                         # 除以0错误
            i,a[1]=1,None                             # 当前操作数a[1]，可以重新输入 
            return
    else:   return
    i,a[0],a[1]=0,None,None
    seg.show(f'{a[3]}') 
try:
    while True:
        button = seg.read()
        if len(button)>0:                             # 有按键按下
            k = keys[button[0]-1]                     # 按键字符
            if k == '=':
                if dot: dot = 0
                calculate() 
            elif k in '+-*/': 
                if dot: dot = 0
                if a[3] is not None and a[0] is None and a[1] is None :
                    # 有上次运算结果，将输入第二个运算数
                    i, a[0]=1,a[3]
                    a[3]=None
                elif a[0] is None: i=0                 # 将输入第一个运算数（防止开始就按下运算符）
                elif a[1] is None: i=1                 # 将输入第二个运算数
                else: calculate()                      # 已有两个运算数，可以计算
                a[2]=k     
            elif k == '.':
                if dot==0:
                    dot = 1
                    if a[i] is None: a[i]=0           # 直接输入小数
                    seg.show(str(a[i])+'.')           # 显示小数点
            else:                                     # 数字
                if a[i] is None: a[i]=0
                if dot:                               # 输入小数部分 
                    a[i]+=round(int(k)/(10**dot),dot)
                    dot += 1
                else:                                 # 输入整数部分 
                    a[i] = a[i]*10+int(k)
                seg.show(str(a[i]))                  # 更新输入显示
        time.sleep_ms(120)                           # 键扫间隔
except KeyboardInterrupt:
    seg.show('')
    seg.power_off()
