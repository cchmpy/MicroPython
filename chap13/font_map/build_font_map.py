import argparse
import struct
import os
import re

# -------------------------- 基本配置 --------------------------
MAGIC_NUMBER = b'FONT'          # 固定魔数
HEADER_SIZE = 16                # 基础头长度（16字节）
DESC_ITEM_SIZE = 12             # 每个字模描述条目长度（12字节）
CHARSET_ASCII = 0x0001          # ASCII字符集类型定义（大端2字节）       
CHARSET_GB2312 = 0x0002         # GB2312字符集类型定义（大端2字节）

# -------------------------- 工具函数 --------------------------
def parse_font_filename(filename):
    """解析字模文件名，提取字符集类型、宽度、高度"""
    pattern = r'^(asc|gb)(\d+)x(\d+)\.fon$'
    match = re.match(pattern, os.path.basename(filename).lower())
    if not match:
        return None
    charset_str = match.group(1)
    width = int(match.group(2))
    height = int(match.group(3))
    # 转换为字符集类型码
    charset = CHARSET_ASCII if charset_str == 'asc' else CHARSET_GB2312
    return charset, width, height

def read_file_bytes(file_path):
    """读取文件所有字节，做基础校验"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{file_path}")
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError(f"空文件：{file_path}")
    with open(file_path, 'rb') as f:
        return f.read()

# -------------------------- 核心生成函数 --------------------------
def build_font_file(map_file, font_files, output_file):
    """
    构建独立字模块的二进制字库文件
    :param map_file: Unicode→GB2312映射文件路径
    :param font_files: 字模文件列表（asc/gb开头）
    :param output_file: 输出文件路径
    """
    # 1. 读取映射文件数据
    map_data = read_file_bytes(map_file)
    map_size = len(map_data)    # 大文件131072字节，小文件48788字节
    
    # 2. 解析所有字模文件，生成独立条目
    font_items = []  # 每个元素：{charset, width, height, size, data, offset}
    for file_path in font_files:
        parse_result = parse_font_filename(file_path)
        if not parse_result:
            raise ValueError(f"文件名格式错误（需asc{w}x{h}.fon/gb{w}x{h}.fon）：{file_path}")
        charset, width, height = parse_result
        size = (width+7)//8*height   # 每个字模的字节长度
        font_data = read_file_bytes(file_path)
        font_items.append({
            'charset': charset,
            'width': width,
            'height': height,
            'size': size,
            'data': font_data})
    if not font_items:
        raise ValueError("未提供有效字模文件")
    
    # 3. 计算各数据块偏移
    desc_item_count = len(font_items)          # 描述条目数量（=字模文件数）
    desc_table_offset = HEADER_SIZE            # 描述表偏移=基础头长度（16字节）
    desc_table_size = desc_item_count * DESC_ITEM_SIZE  # 描述表总长度
    map_data_offset = desc_table_offset + desc_table_size  # 映射数据偏移
    current_offset = map_data_offset + map_size  # 字模数据起始偏移
    
    # 为每个字模条目分配偏移
    for item in font_items:
        item['offset'] = current_offset
        current_offset += len(item['data'])
    
    # 4. 构建基础头（16字节，大端）
    # 格式：>4sHIHI  → 4(魔数)+2(字模规格数量)+4(字模块描述表偏移)+2(编码索引)+4(编码块偏移) = 16字节
    header_pack = struct.pack('>4sHIHI',
        MAGIC_NUMBER,
        desc_item_count,      # 字模规格数量
        desc_table_offset,    # 描述表偏移（固定16）
        0 if map_size>50_000 else 1, # GB2312编码索引类型（0直接索引，1分段索引）
        map_data_offset,      # 编码数据偏移
    )
    assert len(header_pack) == HEADER_SIZE, f"基础头长度必须为{HEADER_SIZE}字节（当前：{len(header_pack)}）"
    
    # 5. 构建字模描述表（每个条目12字节，大端）
    # 格式：>4HI→ 2(字符集类型)+2(宽)+2(高)+2(单字模字节长度)+4(偏移) = 12字节
    desc_table = bytearray()
    for item in font_items:
        desc_pack = struct.pack('>4HI',
            item['charset'],
            item['width'],
            item['height'],
            item['size'],
            item['offset'])
        desc_table.extend(desc_pack)
    assert len(desc_table) == desc_table_size, f"描述表长度错误（预期：{desc_table_size}，实际：{len(desc_table)}）"
    
    # 6. 拼接所有数据并写入输出文件
    with open(output_file, 'wb') as f:        
        f.write(header_pack)     # 写入基础头        
        f.write(desc_table)      # 写入描述表        
        f.write(map_data)        # 写入映射数据        
        for item in font_items:  # 写入所有字模数据块（按条目顺序）
            f.write(item['data'])
    
    # 输出生成信息
    total_size = os.path.getsize(output_file)
    print(f"二进制字库生成成功：{output_file}")
    print(f"生成信息：")
    print(f"   - 基础头长度：{HEADER_SIZE}字节")
    print(f"   - 描述表长度：{desc_table_size}字节（{desc_item_count}个条目）")
    print(f"   - 映射数据长度：{map_size}字节")
    print(f"   - 字模条目详情：")
    for i, item in enumerate(font_items):
        charset_name = "ASCII" if item['charset'] == CHARSET_ASCII else "GB2312"
        print(f"     条目{i+1}：{charset_name} {item['width']}x{item['height']} | 偏移：{item['offset']} | 长度：{len(item['data'])}字节")
    print(f"   - 总文件大小：{total_size}字节")

# -------------------------- 命令行入口 --------------------------
def main():
    parser = argparse.ArgumentParser(description='生成独立字模块的MicroPython二进制字库文件')
    parser.add_argument('-m', '--map', required=True, help='Unicode→GB2312映射二进制文件路径')
    parser.add_argument('-f', '--fonts', required=True, nargs='+', help='字模文件列表（如asc12x12.fon gb16x12.fon）')
    parser.add_argument('-o', '--output', default='font.bin', help='输出文件名（默认：font.bin）')
    args = parser.parse_args()
    
    build_font_file(args.map, args.fonts, args.output)
    print(f'成功生成完整字库文件{args.output}')

if __name__ == '__main__':
    main()
    # Thonny运行参数-m gb2312_code_seg.bin -f font/asc6x12.fon font/gb12x12.fon -o font_12_map_seg.bin
    # Thonny运行参数-m gb2312_code_dir.bin -f font/asc6x12.fon font/gb12x12.fon -o font_12_map_dir.bin
    # 命令行窗口执行：python build_font_map.py -m gb2312_code_dir.bin -f font/asc6x12.fon font/gb12x12.fon font/asc7x14.fon font/gb14x14.fon font/asc8x16.fon font/gb16x16.fon font/asc10x20.fon font/gb20x20.fon font/asc12x24.fon font/gb24x24.fon font/asc14x28.fon font/gb28x28.fon font/asc16x32.fon font/gb32x32.fon -o font_12-32_map_dir.bin
    # 命令行窗口执行：python build_font_map.py -m gb2312_code_seg.bin -f font/asc6x12.fon font/gb12x12.fon font/asc7x14.fon font/gb14x14.fon font/asc8x16.fon font/gb16x16.fon font/asc10x20.fon font/gb20x20.fon font/asc12x24.fon font/gb24x24.fon font/asc14x28.fon font/gb28x28.fon font/asc16x32.fon font/gb32x32.fon -o font_12-32_map_seg.bin