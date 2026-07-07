from machine import UART
from network import PPP
from sys import print_exception
import time, socket, struct

def connect_ppp(uart, timeout=60):                # PPP连接函数,timeout是超时秒数
    def send_at(AT, delay=500):                   # 嵌套函数，封装发送AT指令并打印响应的操作
        nonlocal uart
        uart.read()                               # 清空缓存
        uart.write(f'{AT}\r\n')                   # 发送AT指令
        time.sleep_ms(delay)                      # 延时等待模块的响应
        resp = uart.read()                        # 读取AT指令的响应
        print(f'{AT} → {resp}')                  # 打印响应
        return resp

    # 配置或初始化SIM800L模块
    send_at('AT')                                 # 测试模块响应
    send_at('ATE0')                               # 关闭回显
    send_at('AT+CPIN?')                           # 确认SIM卡就绪
    send_at('AT+CGDCONT=1,"IP","cmnet"')          # 配置接入点名称APN
    send_at('AT+CGATT=1')                         # 附着网络（必须成功）
    resp=send_at('ATD*99***1#')                   # 拨号触发PPP（2G模块核心步骤）
   
    ppp = PPP(uart)
    if b'NO CARRIER' in resp:
        print(f"拨号失败")
    elif b'CONNECT' in resp: 
        print("模块进入PPP模式,启动PPP连接...")
        uart.read()                               # 清空缓存，避免干扰PPP
        ppp.connect()
        while not ppp.isconnected() and timeout>0:
            time.sleep(1)
            timeout -= 1 
        if ppp.isconnected():                     # PPP连接成功
            print(f'PPP连接成功！IP：{ppp.ifconfig()}') 
        else:
            print(f'PPP连接失败, 错误码:{ppp.status()}')
    return ppp

def dns_resolve(domain, dns_server='114.114.114.114', timeout=5):       # 通用DNS解析函数
    # domain:要解析的域名,如www.example.org；参数timeout:超时时间（秒）
    # ns_server: 公共DNS服务器,推荐114.114.114.114
    try:
        # 1. 构建标准DNS查询包（仅解析A记录，适配绝大多数场景）
        dns_header = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0) # 事务ID  

        # 2. 拆分域名为DNS格式（如www.example.org → b'www\x07example\x03org\x00'）
        domain_parts = domain.split('.')
        dns_qname = b''
        for part in domain_parts: dns_qname += struct.pack('B', len(part))+part.encode()
        dns_qname += b'\x00'                                            # 域名结束符
        
        # 3. 查询类型（A记录=1）+查询类（IN=1）
        dns_qtype = struct.pack('!HH', 1, 1)
        # 4. 拼接完整DNS请求包
        dns_request = dns_header + dns_qname + dns_qtype 
        
        # 5. 创建UDP Socket发送请求（SIM800L的PPP仅支持UDP 53）
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(dns_request, (dns_server, 53))
        
        # 6. 接收并解析响应
        resp, _ = sock.recvfrom(1024)
        sock.close()
        
        # 7. 从响应中提取IP（跳过头部12字节+查询段，取回答段的4字节IP）
        if len(resp) < 28: return None                                  # 最小有效响应长度
        ip_start = 12 + len(dns_qname) + 4 + 12                         # 定位回答段的IP位置
        if ip_start + 4 > len(resp): return None
        ip_bytes = resp[ip_start:ip_start+4]                            # IP字节串
        ip = f"{ip_bytes[0]}.{ip_bytes[1]}.{ip_bytes[2]}.{ip_bytes[3]}" # 转换4字节IP为字符串
        return ip                                                       # 返回解析后的IP字符串
    except Exception as err:
        print_exception(err)
        return None
    
def test_connected(domain='www.example.org'):                           # 访问某个网站以检查网络连接
    ip = dns_resolve(domain)                                            # 手动解析IP地址
    print(ip)
    if ip:
        try:
            s = socket.socket()                                         # 定义socket
            s.settimeout(15)
            s.connect((ip, 80))                                         # 连接HTTP服务器 
            s.send(f'GET / HTTP/1.1\r\nHost: {domain}\r\nConnection: close\r\n\r\n')  # 发送HTTP请求头
            print(s.recv(1024))                                         # 打印接收的主页数据
            s.close() 
        except Exception as err: 
            print_exception(err)
    else:
        print('手动解析IP失败，网络连接异常')

if __name__ == '__main__':
    uart = UART(2, baudrate=9600, tx=22, rx=23, timeout=1000)           # 定义串口对象，波特率9600bps
    try:
        ppp = connect_ppp(uart)                                         # PPP连接
        if ppp.isconnected():  test_connected()                         # 测试网络连接
    finally:
        ppp.disconnect()                                                # 关闭PPP连接
