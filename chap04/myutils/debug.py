import time, sys, os, gc                             # gc垃圾收集模块，以后使用
name = {'特殊属性':0,'特殊方法':1,'类':2,'函数或方法':3,'常量':4,'其它':5} # 属性分组名称:对应列表下标
name_ = {v:k for k,v in name.items()}                                 # 键值反转,通过下标获取分组名
length = len(name)
MAX_LOG_SIZE = 1024 * 100                            # 日志文件的最大字节数（100KB，可调整）

def log(message, log_file='log.txt', level='ERROR'): # 写入日志（追加模式）,自动限制文件大小
    path = log_file.rsplit('/',1)                    # 拆分为目录和文件（列表内最多两个元素）
    if len(path)==1:
        directory = '/'
        file = path[0]
    else:
        directory = path[0]
        file = path[1] 
    dt = time.localtime()                            # 获取当前时间
    # 时间格式为：2025-05-20 12:30:45
    dt = f'{dt[0]}-{dt[1]:02d}-{dt[2]:02d} {dt[3]:02d}:{dt[4]:02d}:{dt[5]:02d}'
    try: 
        if file not in os.listdir(directory):        # 检查日志文件是否存在，不存在则创建
            with open(log_file, 'w') as f:
                f.write(f'{dt} [INFO] 日志文件创建成功\n') 
        if os.stat(log_file)[6] >= MAX_LOG_SIZE:     # 限制日志文件大小（超过阈值则清空）
            with open(log_file, 'w') as f:
                f.write(f'{dt} [INFO] 日志文件已清空（超过最大大小）\n') 
        with open(log_file, 'a') as f:               # 追加写入日志（带时间戳和级别）
            f.write(f'{dt} [{level.upper()}] {message}\n')
            if isinstance(message,Exception):        # 如果是异常类对象
                sys.print_exception(message,f)       # 打印详细的异常回溯信息 
    except Exception as err:   print(f'日志写入失败：{err}')

        
def dir1(obj, recursion=True, depth=0, max_depth=4): 
    '''
    以树状形式分组打印obj对象的所有属性
    参数recursion: 当某个属性为类时，是否递归打印该类属性
    参数depth: 缩进层数, 也是递归深度，可用于控制空格的打印数量 
    参数max_depth: 最大递归深度
    '''
    if depth>4: return                     # 限制递归深度    
    members = dir(obj)                     # 取得obj对象的所有属性和方法
    members.sort()
    attr_grp=[[] for i in range(length)]   # 定义分组保存属性名称的列表
    
    # 将对象所有属性分组保存到列表attr_grp
    for x in members: 
        t = getattr(obj,x)                           # 获取字符串x对应的属性
        i = name['其它']                             # attr_grp的下标,用于添加属性，默认是“其它”组
        if (j:=len(x))>4 and x[0:2]=='__' and x[j-2:]=='__':    # 特殊属性或特殊方法
            if callable(t):                                     # 是特殊方法 
                i = name['特殊属性'] if x=='__class__' else name['特殊方法']  # _class__是特殊属性                                                   
            else: i = name['特殊属性']
        else:
            if isinstance(t, (int,float,str)): i = name['常量']
            elif isinstance(t, type): i = name['类'] 
            elif callable(t): i = name['函数或方法']
        attr_grp[i].append(x)
                        
    # 打印obj对象名称和类型
    if depth == 0:                            # 仅初始调用打印对象名称,递归调用中不打印 
        if hasattr(obj,'__qualname__'): print(obj.__qualname__,type(obj))
        elif hasattr(obj,'__name__'):   print(obj.__name__,type(obj))
        else:                           print(obj,type(obj))

    # 分组打印属性
    for i in range(length):
        if len(attr_grp[i])==0: continue                         # 列表中无元素,则不打印
        print(f"{'|   '*depth}|---{name_[i]}")                   # 打印属性分组名称,空格数量是depth倍
        spa = '|   '*(depth+1)                                   # 缩进增加1级，空格数量是depth+1倍
        for x in attr_grp[i]:
            if name_[i]=='特殊属性' or name_[i]=='常量':         # 打印特殊属性或常量的值
                attr_cls = getattr(obj,x)
                if isinstance(attr_cls,str):
                    print(f'{spa}|---{x} = "{attr_cls}"')          # 字符串类型打印引号
                elif not isinstance((temp:=getattr(obj,x)),dict):  # 字典类型内容多不打印                    
                    print(f"{spa}|---{x} = {attr_cls}")
            elif name_[i]=='特殊方法' or name_[i]=='函数或方法': # 方法添加后缀()
                print(f'{spa}|---{x}()')
            elif name_[i]=='其它':                               # 其它属性添加类型信息
                print(f'{spa}|---{x}:{type(getattr(obj,x))}')
            else:                                                # 类
                print(f'{spa}|---{x}')
                if recursion: 
                    dir1(getattr(obj,x),recursion,depth+2,max_depth)       # 递归打印类的属性 

# 装饰器工厂函数-计算函数的执行时间
def timeit(precision='us'):
    def timeit_(func):        
        name = func.__name__ if hasattr(func,'__name__') else '' 
        def wrapper(*args, **kwargs):
            def ticks():   # 嵌套函数，提取重复代码
                if precision=='ms': return time.ticks_ms()
                elif precision=='cpu': return time.ticks_cpu()
                else: return time.ticks_us()
            start = ticks()
            result = func(*args, **kwargs)            
            print(f'{name}() execution time: {time.ticks_diff(ticks(), start)}{precision}')
            return result
        return wrapper
    return timeit_

# 装饰器函数-计算函数分配的内存和产生垃圾的字节大小
def gcit(func, *args, **kwargs): 
    name = func.__name__ if hasattr(func,'__name__') else ''
    def wrapper(*args, **kwargs):
        gc.disable()
        gc.collect()
        a0 = gc.mem_alloc()
        result = func(*args, **kwargs)
        a1 = gc.mem_alloc()        
        gc.collect()        
        print(f'allocated:{a1-a0} garbage:{a1-gc.mem_alloc()}')
        gc.enable()
        return result
    return wrapper

if __name__ == '__main__':
    dir1(dict,True)
    log('test','log.txt','INFO')
    try:
        1/0
    except Exception as err:
        log(err,'sd/log.txt')


