class IncrementalPID:                           # 增量式PID控制器
    def __init__(self, kp, ki, kd, output_min=0, output_max=1023): 
        self.kp = kp; self.ki = ki; self.kd = kd
        self.output_min = output_min
        self.output_max = output_max
        self.reset()                            # 重置PID状态
        
    def reset(self) -> None:                    # 重置PID状态，切换目标/启停时调用，避免输出冲击 
        self._last_error = 0.0                  # e(k-1) 上一次偏差
        self._prev_error = 0.0                  # e(k-2) 上上次偏差
        self._last_output = 0.0                 # u(k-1) 上一次控制量输出

    def compute(self, setpoint, feedback):      # 计算PID输出，需以固定周期调用（如50ms/次）                     
        error = setpoint - feedback             # 本次偏差 e(k)=目标设定值-当前实际值
        # 增量式PID公式
        delta_u = (self.kp * (error - self._last_error)
                 + self.ki * error
                 + self.kd * (error-2*self._last_error+self._prev_error))
        output=self._last_output + delta_u      # 累加得到当前全量输出
        # 输出限幅（防止超出执行器量程，同时抑制积分饱和）
        output = max(self.output_min, min(output, self.output_max))
        # 更新历史状态，为下一次计算做准备
        self._prev_error = self._last_error
        self._last_error = error
        self._last_output = output
        return output                           # 输出限幅后的控制量

class PositionalPID:                            # 位置式PID控制器，适合温控、液位等绝对量控制场景 
    def __init__(self, kp, ki, kd, output_min = 0, output_max = 1023,
                 integral_min = None, integral_max = None):
        # integral_min/max: 积分项限幅，默认与输出范围一致，防止积分饱和
        self.kp = kp; self.ki = ki; self.kd = kd 
        self.output_min = output_min
        self.output_max = output_max
        # 积分限幅，未指定则与输出范围对齐
        self.integral_min = integral_min if integral_min is not None else output_min
        self.integral_max = integral_max if integral_max is not None else output_max 
        self.reset()                            # 重置状态变量

    def reset(self):                            # 重置积分与偏差状态，避免启动超调
        self._integral_sum = 0.0                # 偏差累积和 ∑e(k)
        self._last_error = 0.0                  # 上一次偏差 e(k-1)

    def compute(self, setpoint, feedback):      # 计算PID绝对输出，需固定周期调用
        error = setpoint - feedback
        # 比例项
        p_term = self.kp * error
        # 积分项 + 积分限幅（核心抗饱和措施）
        self._integral_sum += error
        self._integral_sum = max(self.integral_min, min(self._integral_sum, self.integral_max))
        i_term = self.ki * self._integral_sum
        # 微分项
        d_term = self.kd * (error - self._last_error)
        # 总输出 + 输出限幅
        output = p_term + i_term + d_term
        output = max(self.output_min, min(output, self.output_max))
        # 更新状态
        self._last_error = error
        return output                          # 输出限幅后的控制量
