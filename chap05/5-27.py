import io
class LimitedBytesIO(io.BytesIO):
    def __init__(self, max_size):
        super().__init__()
        self.max_size = max_size
    
    def write(self, data):
        if self.tell() + len(data) > self.max_size:
            raise MemoryError("Buffer overflow")
        return super().write(data)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):  # 默认返回None,若有异常继续抛出        
        self.close()        

f = LimitedBytesIO(512)                             # 最大使用512字节内存
f.close()

with LimitedBytesIO(200) as f:
    print(f.write(b'hello,world'))
    f.seek(0)
    print(f.read(10))