from micropython import const
import struct
import bluetooth
# 广播数据类型AD Type
_ADV_TYPE_FLAGS            = const(0x01)  # 标识
_ADV_TYPE_UUID16_MORE      = const(0x02)  # 16-bit服务UUID部分列表
_ADV_TYPE_UUID16_COMPLETE  = const(0x03)  # 16-bit服务UUID完整列表
_ADV_TYPE_UUID32_MORE      = const(0x04)  # 32-bit服务UUID部分列表
_ADV_TYPE_UUID32_COMPLETE  = const(0x05)  # 32-bit服务UUID完整列表
_ADV_TYPE_UUID128_MORE     = const(0x06)  # 128-bit服务UUID部分列表
_ADV_TYPE_UUID128_COMPLETE = const(0x07)  # 128-bit服务UUID完整列表
_ADV_TYPE_NAME             = const(0x09)  # 完整的本地名称
_ADV_TYPE_APPEARANCE       = const(0x19)  # 设备外观
_ADV_TYPE_MANUFACTURER     = const(0xFF)  # 制造商指定数据
_ADV_PAYLOAD_MAX_LEN       = const(31)    # 广播或扫描响应数据包的最大长度

def advertising_payload(limited_disc=False, name=None, services=None, appearance=0, manufacturer=None):
    # 定义并返回广播数据和扫描响应数据；参数limited_disc：有限可发现模式
    adv_data = bytearray(); resp_data = bytearray() 
    def _append(adv_type, value):         # 嵌套函数，先向广播包添加，若满放入扫描响应包
        nonlocal adv_data, resp_data
        data = struct.pack("BB", len(value)+1, adv_type) + value
        if len(data)+len(adv_data) <= _ADV_PAYLOAD_MAX_LEN:    adv_data += data
        elif len(data)+len(resp_data) <= _ADV_PAYLOAD_MAX_LEN: resp_data += data
        else: raise ValueError(f'广播或扫描响应数据包长度超过{_ADV_PAYLOAD_MAX_LEN}字节！')
    
    # 1、添加flags
    _append(_ADV_TYPE_FLAGS,struct.pack('B', (0x01 if limited_disc else 0x02) | 0x04)) 
    # 2、添加广播名称，name是字符串类型
    if name:  _append(_ADV_TYPE_NAME, name.encode())
    # 3、添加服务，服务是uuid类型的列表
    if services:
        for uuid in services:
            b = bytes(uuid)
            if len(b) == 2:    _append(_ADV_TYPE_UUID16_COMPLETE, b)
            elif len(b) == 4:  _append(_ADV_TYPE_UUID32_COMPLETE, b)
            elif len(b) == 16: _append(_ADV_TYPE_UUID128_COMPLETE, b)
            else: raise ValueError(f'服务对应的uuid长度是{len(b)},应为2、4、16字节。')
    # 4、添加外观，默认为0，非0时添加，appearance是16-bit整数
    if appearance: _append(_ADV_TYPE_APPEARANCE, struct.pack('<H', appearance)) 
    # 5、添加厂商数据，manufacturer是2个元素的列表，第一个元素是厂商ID,第二个是数据
    if manufacturer:
        _append(_ADV_TYPE_MANUFACTURER,struct.pack('<H',manufacturer[0]) + manufacturer[1]) 
    return adv_data, resp_data

def decode_field(payload, adv_type):      # 解析类型为adv_type的广播数据
    # payload是bytes或bytearray对象
    i= 0;  result=[] 
    while i + 1 < len(payload):
        if payload[i + 1] == adv_type:    # 判断类型
            result.append(payload[i + 2 : i + payload[i] + 1])
        i += 1 + payload[i]
    return result

def decode_name(payload):                 # 解析广播数据中的名称
    name = decode_field(payload, _ADV_TYPE_NAME)        # 解析完整的名称
    if len(name)==0: 
        name = decode_field(payload, _ADV_TYPE_NAME-1)  # 解析剪裁的名称
    return name[0].decode() if name else ''

def decode_services(payload):            # 解析广播数据中的服务列表
    services = []
    for type_uuid in range(_ADV_TYPE_UUID16_MORE, _ADV_TYPE_UUID128_COMPLETE+1):
        for u in decode_field(payload, type_uuid):
            services.append(bluetooth.UUID(u))
    return services
    
if __name__ == "__main__":
    try:
        adv_data, resp_data = advertising_payload(
            name="esp32_temp", appearance=0x0300,
            services=[bluetooth.UUID(0x181A), bluetooth.UUID(0x180F)],
            manufacturer=[0xF000,'厂商数据'.encode()],
        )
    except ValueError as err: print(err)
    print(adv_data)
    print(resp_data)
    print(decode_name(adv_data))
    print(decode_services(adv_data))
