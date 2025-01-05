class TestWorkflowManager:
    def __init__(self, chat):
        self.chat = chat
        self.visited_states = set()  # 记录已访问的状态
        self.failed_operations = {}  # 记录失败的操作
        self.test_progress = {}  # 记录测试进度
        self.strategy_adjustments = []  # 记录策略调整历史
        
    def get_state_signature(self, activity_name, components):
        """生成界面状态的唯一标识"""
        components_str = ','.join(sorted([c['@desc'] for c in components if '@desc' in c]))
        return f"{activity_name}:{components_str}"
        
    def should_explore_state(self, activity_name, components):
        """判断是否应该探索当前状态"""
        state_sig = self.get_state_signature(activity_name, components)
        if state_sig in self.visited_states:
            return False
        self.visited_states.add(state_sig)
        return True
        
    def record_failed_operation(self, operation, error):
        """记录失败的操作"""
        if operation not in self.failed_operations:
            self.failed_operations[operation] = []
        self.failed_operations[operation].append(error)
        
    def get_recovery_action(self, current_state):
        """获取恢复操作"""
        prompt = f"""
当前界面状态出现异常:
{current_state}

历史失败操作:
{self.failed_operations}

请提供恢复建议:
1. 是否需要返回上一页?
2. 是否需要重启应用?
3. 其他可能的恢复操作?
"""
        response = self.chat.send_message(prompt)
        return response
        
    def adjust_test_strategy(self):
        """根据测试历史调整测试策略"""
        prompt = f"""
测试执行情况:
- 已访问状态数: {len(self.visited_states)}
- 失败操作数: {len(self.failed_operations)}
- 当前测试进度: {self.test_progress}

请提供策略调整建议:
1. 是否需要改变测试深度?
2. 是否需要关注特定类型的组件?
3. 是否需要避免某些操作序列?
"""
        response = self.chat.send_message(prompt)
        self.strategy_adjustments.append(response)
        return response