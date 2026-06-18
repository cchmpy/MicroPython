class Shape:
    def __init__(self, name): self.name = name 
    def area(self): raise NotImplementedError
 
    @staticmethod
    def create_circle(radius): return Circle(radius) 
    @staticmethod
    def create_rectangle(width, height): return Rectangle(width, height)

class Circle(Shape):
    def __init__(self, radius):
        super().__init__("Circle")                     # 初始化父类
        self.radius = radius    
    def area(self): return 3.14159 * self.radius ** 2

class Rectangle(Shape):
    def __init__(self, width, height):
        super().__init__("Rectangle")
        self.width = width
        self.height = height    
    def area(self): return self.width * self.height

circle = Shape.create_circle(5)                       # 使用工厂方法创建对象
print(f"{circle.name} area: {circle.area():.2f}")     # 输出: Circle area: 78.54
rect = Shape.create_rectangle(4, 6)                   # 使用工厂方法创建对象
print(f"{rect.name} area: {rect.area()}")             # 输出: Rectangle area: 24
