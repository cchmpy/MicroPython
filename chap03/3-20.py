class AppConfig:
    _instance = None    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_config()   # 初始化配置
        return cls._instance    
    def load_config(self):
        self.debug_mode = True            # 模拟加载配置
config1 = AppConfig()
config2 = AppConfig()
print(config1 is config2)                 # 输出: True (同一实例)
