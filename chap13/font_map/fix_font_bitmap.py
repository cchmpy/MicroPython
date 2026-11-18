import os

# 定义ASCII可显示字符范围（32-126）
ASCII_PRINTABLE = set(range(32, 127))

def is_gb2312_empty(zone: int, pos: int) -> bool:
    """
    通过解码验证判断GB2312的区/位是否为空码位
    :param zone: 区码（1-87）
    :param pos: 位码（1-94）
    :return: True=空码位（解码失败），False=有效码位（解码成功）
    """
    # 区码和位码必须在1-94范围内（GB2312标准）
    if not (1 <= zone <= 94) or not (1 <= pos <= 94):
        return True
    
    # 转换区/位为GB2312对应的字节（核心规则：区/位 + 0xA0）
    b1 = zone + 0xA0  # 区码转第一个字节
    b2 = pos + 0xA0   # 位码转第二个字节
    gb_bytes = bytes([b1, b2])
    
    # 尝试解码，失败则判定为空码位
    try:
        gb_bytes.decode('gb2312')
        return False  # 解码成功=有效码位
    except UnicodeDecodeError:
        return True   # 解码失败=空码位

def parse_font_filename(filename: str) -> tuple:
    """
    解析字模文件名，提取字符集类型、宽度、高度
    :param filename: 文件名（如asc6x12.fon、gb16x16.fon）
    :return: (字符集类型, 宽度, 高度) 或 (None, None, None)
    """
    # 去掉文件后缀
    name_without_ext = os.path.splitext(filename)[0]
    
    # 判断字符集类型
    if name_without_ext.startswith('asc'):
        charset = 'asc'
        size_part = name_without_ext[3:]  # 截取asc后的部分（如6x12）
    elif name_without_ext.startswith('gb'):
        charset = 'gb'
        size_part = name_without_ext[2:]  # 截取gb后的部分（如16x16）
    else:
        return None, None, None
    
    # 拆分宽度和高度
    if 'x' not in size_part:
        return None, None, None
    try:
        w_str, h_str = size_part.split('x', 1)
        width = int(w_str)
        height = int(h_str)
        return charset, width, height
    except ValueError:
        return None, None, None

def process_single_font_file(filepath: str):
    """
    处理单个字模文件，替换空码位为0xFF
    :param filepath: 文件完整路径
    """
    filename = os.path.basename(filepath)
    # 解析文件名
    charset, w, h = parse_font_filename(filename)
    if not all([charset, w, h]):
        print(f"[跳过] 无效文件名：{filename}")
        return
    
    # 计算每个字符的字模字节数
    byte_per_char = (w + 7) // 8 * h
    print(f"[处理] {filename} | 字符集：{charset} | 尺寸：{w}x{h} | 每字符字节数：{byte_per_char}")
    
    # 读取二进制数据（bytearray支持原地修改）
    try:
        with open(filepath, 'rb') as f:
            data = bytearray(f.read())
    except Exception as e:
        print(f"[错误] 读取文件{filename}失败：{e}")
        return
    
    # 验证文件长度是否符合预期
    total_chars = 128 if charset == 'asc' else 87 * 94  # ASCII=128个，GB2312=8178个
    expected_len = total_chars * byte_per_char
    if len(data) != expected_len+2:   # 文件末尾有回车换行两个字节
        print(f"[警告] {filename} 文件长度异常（实际{len(data)}字节，预期{expected_len}字节），跳过")
        return
    
    # 遍历所有字符，替换空码位
    for char_idx in range(total_chars):
        start = char_idx * byte_per_char
        end = start + byte_per_char
        
        # 判断是否为空码位
        need_replace = False
        if charset == 'asc':
            # ASCII：字符编码=索引，非可显示字符需要替换
            char_code = char_idx
            need_replace = char_code not in ASCII_PRINTABLE
        elif charset == 'gb':
            # GB2312：索引转区/位（idx从0开始，区=1-87，位=1-94）
            zone = (char_idx // 94) + 1
            pos = (char_idx % 94) + 1
            need_replace = is_gb2312_empty(zone, pos)
        
        # 替换为0xFF
        if need_replace:
            data[start:end] = b'\xFF' * (end - start)
    
    # 备份原文件（仅备份一次）
    backup_path = filepath + '.bak'
    if not os.path.exists(backup_path):
        try:
            os.rename(filepath, backup_path)
            print(f"[备份] 原文件已保存至：{os.path.basename(backup_path)}")
        except Exception as e:
            print(f"[错误] 备份文件{filename}失败：{e}")
            return
    
    # 写入处理后的数据
    try:
        with open(filepath, 'wb') as f:
            f.write(data[:expected_len])  # 去掉最后2个字节
        print(f"[完成] {filename} 处理完毕\n")
    except Exception as e:
        print(f"[错误] 写入文件{filename}失败：{e}\n")

def main():
    """主函数：遍历font文件夹处理所有字模文件"""
    font_folder = 'font'
    # 检查文件夹是否存在
    if not os.path.exists(font_folder):
        print(f"[错误] 文件夹{font_folder}不存在，请确认路径！")
        return
    
    # 遍历文件夹下所有文件
    for filename in os.listdir(font_folder):
        filepath = os.path.join(font_folder, filename)
        if os.path.isfile(filepath):
            process_single_font_file(filepath)
    
    print("所有文件处理完成！")

if __name__ == '__main__':
    main()