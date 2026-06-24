import uctypes,struct
class WavFile:    
    # WAV文件头部结构描述符
    WAV_HEADER_DESC = {
        "riff_id":(0 | uctypes.ARRAY, 4 | uctypes.UINT8),
        "size":    4 | uctypes.UINT32,
        "format": (8 | uctypes.ARRAY, 4 | uctypes.UINT8),
        "fmt_id":       (12 | uctypes.ARRAY, 4 | uctypes.UINT8),
        "fmt_size":      16 | uctypes.UINT32,
        "encode":        20 | uctypes.UINT16,
        "channels":      22 | uctypes.UINT16,
        "sample_rate":   24 | uctypes.UINT32,
        "bytes_per_sec": 28 | uctypes.UINT32,
        "bytes_per_sam": 32 | uctypes.UINT16,
        "sample_bits":   34 | uctypes.UINT16, 
        "data_id": (36 | uctypes.ARRAY, 4 | uctypes.UINT8),
        "data_size":40 | uctypes.UINT32 }
    
    def __init__(self,wav_file, *, bufsize=12000, new=False, channels=1,sample_rate=11025,sample_bits=16):       
        self._new = new                                    # 是否新建wav文件
        if new:
            self.wav = open(wav_file,'wb')                 # 新建一个wav文件                                
            self.wav.write(struct.pack('<4sI4s4sI2H2I2H4sI',b'RIFF',0,b'WAVE',b'fmt ',
                             16, 1, channels, sample_rate,
                             channels*sample_rate*sample_bits//8,
                             channels*sample_bits//8,
                             sample_bits,b'data',0))       # 写入文件头数据
            self.channels    = channels                    # 声道数
            self.sample_rate = sample_rate                 # 采样率
            self.sample_bits = sample_bits                 # 采样位数
        else:
            try:
                self.wav  = open(wav_file,'rb')            # 打开现有的wav文件
                self._parse_header()                       # 解析文件头
                self._buf = memoryview(bytearray(bufsize)) # 读缓冲区
            except OSError:
                raise OSError(f'Failed to open, "{wav_file}" may not exist')
        
    def close(self):                                       # 关闭wav文件 
        try: self.wav.close()
        except: pass
  
    def _parse_header(self):                               # 解析wav文件头
        header_data = self.wav.read(44)                    # 读取头部数据
        addr = uctypes.addressof(header_data)
        self.header = header = uctypes.struct(addr,self.WAV_HEADER_DESC,uctypes.LITTLE_ENDIAN)
        if bytes(header.format) != b'WAVE' or header.encode!=1:      # 有效性检查
            self.close()
            raise ValueError("Not a WAV file or not encoded in PCM.")
        self.channels    = header.channels
        self.sample_rate = header.sample_rate
        self.sample_bits = header.sample_bits
        
    def read(self):                                        # 读取采样点数据（生成器模数）
        if self._new: return None
        self.wav.seek(44)
        while size := self.wav.readinto(self._buf): 
            if size==len(self._buf): yield self._buf
            elif size<len(self._buf): yield self._buf[:size] 
          
    def write(self,data):                                  # 向新建文件内写入采样点数据data
        self.wav.write(data) 
    
    def __str__(self):                                     # 打印wav文件信息        
        return f'''Channels: {self.channels}
Sample Rate: {self.sample_rate} Hz
Sample Bits: {self.sample_bits}\n'''           
            
    def __enter__(self):                                   # 实现上下文协议，入口函数。可使用with语句
        return self       
    def __exit__(self,*args):                              # 实现上下文协议，出口函数。
        self.close() 
    
if __name__ == '__main__':    
    with WavFile('/sd/jys8_11k.wav') as f:
        print(f)
        with WavFile('/sd/jys8_11k_bk.wav',new=True, channels=f.channels,
                     sample_rate=f.sample_rate, sample_bits=f.sample_bits) as newfile:
            for data in f.read(): newfile.write(data)      # 读取源文件的采样点数据，并写入新文件 
            print(newfile)
