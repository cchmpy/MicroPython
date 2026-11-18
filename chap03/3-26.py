# 示例1：限制暴露的属性和方法
class Restricted:
    def __init__(self):
        self.public = "I'm public"
        self._internal = "I'm internal"    
    def __dir__(self):
        return ["public"]  # 只返回 public 实例变量，隐藏 _internal
print(dir(Restricted()))  # 输出 ['public']（不显示 _internal）



# 示例2：动态生成属性列表
class DynamicAttrs:
    def __getattr__(self, name):       # 访问不存在的属性时调用该方法
        if name == 'x': return 100     # 为x属性提供默认值
        elif name == 'y': return 999   
        else:
            raise AttributeError(f"'{self.__qualname__}' object has no attribute '{name}'") 
    def __dir__(self):
        return ["x", "y"]              # 提示用户可访问的虚拟属性
obj = DynamicAttrs()
print(dir(obj))                       # 输出:['x', 'y']
print(obj.x)                          # 输出:100
print(obj.z)     # AttributeError: 'DynamicAttrs' object has no attribute 'z'
