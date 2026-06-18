import sys
call_count = {}                     # 定义全局变量，保存函数调用的次数
def tracefunc(frame, event, arg):   # 定义跟踪函数
    filename = frame.f_code.co_filename
    lineno = frame.f_lineno
    func = frame.f_code.co_name    
    print(f"{event:10} | {filename}:{lineno} | {func}() | {arg}") # 打印所有事件的信息    
    # 特殊事件处理
    if event == 'call':
        if func == 'test1':
            return None                                  # 跳过test1函数的跟踪
        elif func == 'test2':
            call_count[func] = call_count.get(func, 0)+1 # 记录test2函数的调用次数
    elif event == 'line':
        pass
    elif event == 'return':
        pass
    elif event == 'exception':
        pass    
    return tracefunc      # 继续使用同一跟踪函数
sys.settrace(tracefunc)   # 设置跟踪函数
def test1(a=0,b=0):       # 测试函数
    x = 2*a
    x += b**2
    return x
def test2():              # 测试函数
    a = b'abc'
    m = bytearray(30)
    m[:3]= a
    test1(m[0],m[1])
    return None
def main():               # 测试函数
    test2()
    try: 1/0              # 抛出异常
    except: pass
x = 10                    # 定义全局变量
y = 100                   # 定义全局变量
main()
print(call_count)
sys.settrace(None)        # 禁用跟踪