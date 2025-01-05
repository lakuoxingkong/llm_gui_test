class StateValidator:
    def __init__(self, chat):
        self.chat = chat
        self.expected_states = {}
        self.current_state = {}
        
    def record_expected_state(self, operation, expected_changes):
        """记录操作后的预期状态"""
        self.expected_states[operation] = expected_changes
        
    def _get_component_desc(self, component):
        """安全地获取组件描述"""
        if '@desc' in component:
            return component['@desc']
        # 尝试从其他属性构建描述
        text = component.get('@text', '')
        content = component.get('@content-desc', '')
        rid = component.get('@resource-id', '').split('/')[-1].replace('_', ' ')
        
        if text:
            return text
        elif content:
            return content
        elif rid:
            return rid
        return "unknown_component"
        
    def capture_current_state(self, components_list, activity_name):
        """捕获当前界面状态"""
        try:
            visible_components = []
            for comp in components_list:
                if isinstance(comp, dict):  # 验证组件数据有效
                    desc = self._get_component_desc(comp)
                    if desc:
                        visible_components.append(desc)
                        
            self.current_state = {
                'activity': activity_name,
                'visible_components': visible_components,
                'editable_values': self._get_editable_values(components_list)
            }
        except Exception as e:
            print(f"Error capturing state: {str(e)}")
            # 设置一个基本状态防止后续处理崩溃
            self.current_state = {
                'activity': activity_name,
                'visible_components': [],
                'editable_values': {}
            }
        
    def _get_editable_values(self, components_list):
        """获取所有可编辑组件的值"""
        editable_values = {}
        for comp in components_list:
            if not isinstance(comp, dict):
                continue
            if '@class' in comp and comp['@class'] in [
                'android.widget.EditText', 
                'android.widget.AutoCompleteTextView'
            ]:
                desc = self._get_component_desc(comp)
                editable_values[desc] = comp.get('@text', '')
        return editable_values
        
    def verify_state(self, operation):
        """验证当前状态是否符合预期"""
        if not self.current_state:
            return "状态验证失败: 无法获取当前状态"
            
        prompt = f"""
当前界面状态:
- Activity: {self.current_state['activity']}
- 可见组件: {', '.join(self.current_state['visible_components'])}
- 可编辑值: {self.current_state['editable_values']}

执行的操作: {operation}

预期状态:
{self.expected_states.get(operation, '无预期状态')}

请判断当前状态是否符合预期，并给出分析:
1. 状态是否匹配 (Yes/No)
2. 如果不匹配，具体哪些地方存在问题
"""
        try:
            response = self.chat.send_message(prompt)
            return response
        except Exception as e:
            return f"状态验证过程出错: {str(e)}"