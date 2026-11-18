
def build_unicode_to_gb2312_map():
    """
    构建Unicode编码到GB2312编码的映射字典
    返回：dict，key=Unicode编码(int)，value=GB2312编码(bytes，2字节)
    """   
    unicode_to_gb2312 = {}    
    for qu in range(0xA1, 0xF8):                     # GB2312区码范围：0xA1 ~ 0xF7，共87个区       
        for wei in range(0xA1, 0xFF):                # GB2312位码范围：0xA1 ~ 0xFE，共94个位
            gb2312_bytes = bytes([qu, wei])
            try:                
                char = gb2312_bytes.decode('gb2312') # 解码GB2312字节为Unicode字符
                uni = ord(char)                      # 字符的Unicode码位值   
                unicode_to_gb2312[uni]=gb2312_bytes  # 添加字典项
            except UnicodeDecodeError:                
                continue                             # 跳过无效的GB2312编码组合
    return unicode_to_gb2312                         # 返回字典对象          

def build_gb_lut_direct(unicode_map, output_file='gb2312_code_dir.bin'):
    """
    直接索引法：Unicode编码直接作为索引，存储对应的GB2312编码
    :param unicode_map: Unicode→GB2312映射字典
    :param output_file: 输出文件名
    """   
    buffer = bytearray([0xFF])*((0xFFFF + 1) * 2)    # 初始化字节数组：每个Unicode码位对应2字节，初始值0xFFFF    
    for uni, gb in unicode_map.items():              # 填充映射的GB2312编码
        if uni > 0xFFFF: continue                    # 跳过超出指定范围的Unicode
        addr = uni * 2                               # 计算偏移量（每个Unicode占2字节）
        buffer[addr:addr+2] = gb                     # 写入GB2312区码和位码    
    with open(output_file, 'wb') as f:               # 把数据写入二进制文件
        f.write(buffer)      
    print(f'已生成直接索引法的GB2312查找表文件{output_file}')

def build_gb_lut_segment(unicode_map, output_file='gb2312_code_seg.bin'):
    """
    分段索引法：按指定Unicode区段存储，节省空间
    :param unicode_map: Unicode→GB2312映射字典
    :param output_file: 输出文件名
    """
    sections = [(0x0000, 0x0451),(0x2015, 0x2642),(0x3000, 0x3229),
                (0x4E00, 0x9FA0),(0xFF01, 0xFFFF)]   # Unicode区段（起始, 结束） 
    buffer = bytearray()                             # 待写入的缓冲区
    for start, end in sections:                      # 按区段写入GB2312编码
        for uni in range(start, end + 1):
            gb = unicode_map.get(uni, b'\xFF\xFF')   # 无映射则填充0xFFFF
            buffer.extend(gb)                        # 将GB2312编码写入缓冲区
    
    with open(output_file, 'wb') as f:               # 把数据写入二进制文件
        f.write(buffer)      
    print(f'已生成分段索引法的GB2312查找表文件{output_file}')

def main(): 
    unicode_map = build_unicode_to_gb2312_map()
    print('完成构建映射表')    
    build_gb_lut_direct(unicode_map)
    build_gb_lut_segment(unicode_map)    

if __name__ == '__main__':
    main()


