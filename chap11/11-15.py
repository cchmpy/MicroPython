from ahttp import Application, Response  # 导入程序11-13.py（ahttp.py）
from micropython import const
from random import randint
from machine import PWM
import json
HTML_DOC = const('''<!DOCTYPE html><html lang="zh-CN"><head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 在线监控</title>
</head><body>
    <div style="text-align:center;">
        <h1>ESP32 监控中心</h1>
        <p>温度：<strong id="temp">℃</strong></p>
        <p>湿度：<strong id="humi">%</strong></p>
        <p>LED亮度: <strong id="brig"></strong></p>
        <p><input type="range" id="rang" title="设置亮度" min="0" max="100" value=0><span id="rangHint"></span></p>
        <p><span id="status"></span></p>
    </div>
    <script>
        const tempText = document.getElementById('temp');
        const humiText = document.getElementById('humi');
        const brigText = document.getElementById('brig');
        const rangeInput = document.getElementById('rang');
        const rangeHint = document.getElementById('rangHint');
        const statusText = document.getElementById('status');
        // 封装fetch的模板函数
        async function request(url, options = {}, timeout = 5000) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => { controller.abort(); }, timeout);
            try {
                const response = await fetch(url, { ...options, signal: controller.signal });
                clearTimeout(timeoutId);
                if (response.ok) { 
                    const data = await response.json();
                    tempText.innerText = `${data.temp}℃`;    //反引号(~键)模板字符串
                    humiText.innerText = `${data.humi}%`;
                    brigText.innerText = `${data.brig}%`;
                    statusText.innerText = data.status;
                }
            } catch (error) {
                clearTimeout(timeoutId);
                clearInterval(refreshTimer);
                statusText.innerText = '网络异常,设备离线'; 
            }
        }
        async function setBright(){
            request('/set/bright', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', },
                        body: JSON.stringify({brig: rangeInput.value})
                        },5000);
        }
        // 添加range的3个事件（input事件实时触发，滑动过程中会执行）
        rangeInput.addEventListener('input', ()=>{rangeHint.innerText = rangeInput.value;});
        rangeInput.addEventListener('touchend',setBright);    // 触摸结束(手机等移动端)
        rangeInput.addEventListener('mouseup', setBright);    // 鼠标释放
        // 每5秒刷新一次设备数据
        let refreshTimer = setInterval(()=>{request('/update')}, 5000);
        request('/update');                                   // 载入页面后执行一次刷新
</script></body></html>''')

class EquipmentControl:
    def __init__(self,led_pin, dht11_pin=None, host='0.0.0.0'):
        self._params = {'temp':0,'humi':0,'brig':0,'status':''}# 设备参数:温度、湿度、亮度、状态信息
        self._pwm = PWM(led_pin,freq=1000, duty_u16=0)         # pwm对象:led亮度控制 
        app = Application()
        app.add_routes([('/', self._index_handler),                 # 路径"/"的处理协程
                        ('/update',self._update_handler),           # 路径"/update"的处理协程
                        ('/set/bright',self._set_bright_handler)])  # 路径"/set/bright"的处理协程
        app.run(host=host)
    
    def _response(self,status):                                # 创建并返回Response对象
        self._params['temp'] = randint(0,40)                   # 用随机数模拟测量温湿度 
        self._params['humi'] = randint(10,90)
        self._params['status'] = status
        return Response(headers={'Content-Type': 'application/json; charset=utf-8'}, 
                        body=json.dumps(self._params))
    
    async def _index_handler(self,request):                    # 定义路径"/"(主页)的处理协程
        return Response(headers={'Content-Type': 'text/html'}, body=HTML_DOC)
    
    async def _update_handler(self,request):                   # 定义路径"/update"的处理协程
        return self._response('设备在线')
    
    async def _set_bright_handler(self,request):               # 定义路径"/set/bright"的处理协程
        b = request.json().get('brig',None)                    # 获取要设置的亮度值
        if b:                                                  # 设置亮度
            self._params['brig'] = int(b)
            self._pwm.duty_u16(int(b)*65535//100)
            status = '设置亮度成功'
        else: status ='设置亮度失败'
        return self._response(status) 
if __name__ == '__main__':
    import myutils
    wlan=myutils.connect_wifi()
    EquipmentControl(led_pin=23,host=wlan.ifconfig()[0])       # 启动服务器 
