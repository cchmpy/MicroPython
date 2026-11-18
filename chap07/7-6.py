from machine import disable_irq, enable_irq
class Mutex:                    #互斥锁类
    def __init__(self):
        self._locked = False    
    def acquire(self):          # 获取锁
        state = disable_irq()   # 禁用中断（开始关键操作），必需在检查self._locked前 
        if self._locked:        # 检查并设置锁 
            enable_irq(state)   # 锁已被占用
            return False
        else:                   # 获取锁成功 
            self._locked = True
            enable_irq(state)   # 恢复中断
            return True
    def release(self):          # 释放锁 
        state = disable_irq()   # 禁用中断
        self._locked = False 
        enable_irq(state)       # 恢复中断 
    def is_locked(self):        
        return self._locked     # 不需要禁用中断，因为读取布尔值是原子的

if __name__ == '__main__': 
    mutex = Mutex()    
    def main():                 # 主程序处理方式
        if mutex.acquire():
            try:
                ...            # 此次访问共享数据
            finally:
                mutex.release() 
    def isr():                 # ISR的处理方式
        if not mutex.is_locked():
            ...                # 此处访问共享数据
        else:
            ...                # 无法获取锁，可采用跳过本次处理或其它措施