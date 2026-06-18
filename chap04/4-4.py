def calculate_operations(numbers):   
    def sum_of_squares():    # 辅助函数：平方和（只在 calculate_operations 内部使用）
        return sum(x ** 2 for x in numbers)       
    def sum_of_cubes():      # 辅助函数：立方和
        return sum(x ** 3 for x in numbers)    
    return {"squares": sum_of_squares(),
            "cubes": sum_of_cubes()}
print(calculate_operations([1, 2, 3]))  # 输出: {'cubes': 36, 'squares': 14}
