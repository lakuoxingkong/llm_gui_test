class GPTDroidTester:
    def __init__(self, app_name):
        self.app_name = app_name
        self.current_page = None
        self.activity_path = []
        self.tested_widgets = {}
        self.function_status = {}
        self.gui_context = {}

    # 主要的测试执行函数
    def execute_testing(self):
        while True:
            # 获取当前页面的GUI上下文信息
            self.extract_gui_context()
            # 生成并执行操作
            operation = self.generate_and_execute_operation()
            if operation is None:
                break
            # 检查操作执行结果和应用状态
            if not self.check_operation_execution(operation):
                self.handle_failed_operation(operation)
            # 更新测试进度和状态信息
            self.update_testing_status(operation)

    def extract_gui_context(self):
        app_info = self.extract_app_info()
        page_gui_info = self.extract_page_gui_info()
        widget_info = self.extract_widget_info()
        self.gui_context = {
            "app_info": app_info,
            "page_gui_info": page_gui_info,
            "widget_info": widget_info
        }

    def extract_app_info(self):
        # 假设这里通过解析AndroidManifest.xml文件获取应用信息
        app_info = {
            "name": self.app_name,
            "activities": []  # 待填充实际的活动列表
        }
        return app_info

    def extract_page_gui_info(self):
        # 假设通过UIAutomator获取当前页面的视图层次结构文件
        view_hierarchy = self.get_view_hierarchy()
        page_name = view_hierarchy["activity_name"]
        widgets = []
        upper_widgets = []
        lower_widgets = []
        for widget in view_hierarchy["widgets"]:
            widgets.append(widget["text"] or widget["resource-id"])
            if widget["position"] == "upper":
                upper_widgets.append(widget["text"] or widget["resource-id"])
            else:
                lower_widgets.append(widget["text"] or widget["resource-id"])
        page_gui_info = {
            "activity_name": page_name,
            "widgets": widgets,
            "upper": upper_widgets,
            "lower": lower_widgets
        }
        return page_gui_info

    def extract_widget_info(self):
        view_hierarchy = self.get_view_hierarchy()
        widget_info_list = []
        for widget in view_hierarchy["widgets"]:
            widget_info = {
                "text": widget["text"],
                "hint_text": widget["hint-text"],
                "resource_id": widget["resource-id"],
                "category": widget["class"],
                "action": widget["clickable"],
                "nearby_widget": self.get_nearby_widget_text(widget)
            }
            widget_info_list.append(widget_info)
        return widget_info_list

    def get_nearby_widget_text(self, widget):
        view_hierarchy = self.get_view_hierarchy()
        nearby_widget_text = ""
        # 查找父节点部件文本
        parent_widget = self.find_parent_widget(widget, view_hierarchy)
        if parent_widget:
            nearby_widget_text += f"Parent: {parent_widget['text']}, "
        # 查找兄弟节点部件文本
        sibling_widgets = self.find_sibling_widgets(widget, view_hierarchy)
        for sibling in sibling_widgets:
            nearby_widget_text += f"Sibling: {sibling['text']}, "
        return nearby_widget_text

    def find_parent_widget(self, widget, view_hierarchy):
        for w in view_hierarchy["widgets"]:
            if widget["parent_id"] == w["resource-id"]:
                return w
        return None

    def find_sibling_widgets(self, widget, view_hierarchy):
        sibling_widgets = []
        for w in view_hierarchy["widgets"]:
            if w["parent_id"] == widget["parent_id"] and w["resource-id"] != widget["resource-id"]:
                sibling_widgets.append(w)
        return sibling_widgets

    def generate_and_execute_operation(self):
        prompt = self.generate_gui_prompt()
        operation = query_large_model(prompt)
        if operation:
            self.execute_operation(operation)
            return operation
        return None

    def generate_gui_prompt(self):
        app_info = self.gui_context["app_info"]
        page_gui_info = self.gui_context["page_gui_info"]
        widget_info = self.gui_context["widget_info"]
        prompt = f"We want to test the {app_info['name']} App. It has the following activities, including {', '.join(app_info['activities'])}. The current page is {page_gui_info['activity_name']}, it has {', '.join(page_gui_info['widgets'])}. The upper part of the app is {', '.join(page_gui_info['upper'])}, the lower part of the app is {', '.join(page_gui_info['lower'])}. The widgets which can be operated are {', '.join([w['text'] or w['resource_id'] for w in widget_info])}."
        for w in widget_info:
            prompt += f" {w['text'] or w['resource_id']} is {w['category']} which can {w['action']} and its nearby widget is {w['nearby_widget']}."
        prompt += " What operation is required? (<Operation>[click / double-click / long press / scroll]+<Widget Name>)"
        return prompt

    def execute_operation(self, operation):
        if "click" in operation:
            widget_name = operation.split('"')[1]
            # 假设这里通过ADB或Appium执行点击操作
            execute_adb_click(widget_name)
        elif "input" in operation:
            parts = operation.split('"')
            widget_name = parts[1]
            input_text = parts[3]
            # 假设这里通过ADB或Appium执行输入操作
            execute_adb_input(widget_name, input_text)

    def check_operation_execution(self, operation):
        prompt = f"Did the operation {operation} succeed?"
        result = query_large_model(prompt)
        return result == "Yes"

    def handle_failed_operation(self, operation):
        prompt = f"The operation {operation} failed. Please suggest a new operation."
        new_operation = query_large_model(prompt)
        self.execute_operation(new_operation)

    def update_testing_status(self, operation):
        # 更新活动路径
        self.activity_path.append(self.gui_context["page_gui_info"]["activity_name"])
        # 更新已测试部件信息
        widget_name = operation.split('"')[1]
        if widget_name in self.tested_widgets:
            self.tested_widgets[widget_name] += 1
        else:
            self.tested_widgets[widget_name] = 1
        # 更新功能状态（假设通过询问LLM获取当前测试的功能状态）
        function_name, status = self.query_function_status()
        self.function_status[function_name] = status

    def query_function_status(self):
        prompt = "What function is currently being tested? Are we testing a new function? (<FunctionName> + <Status>)"
        result = query_large_model(prompt)
        function_name, status = result.split(" + ")
        return function_name, status

def query_large_model(prompt):
    # 这里模拟向大模型发送请求并获取回复
    response = requests.post("YOUR_LARGE_MODEL_API_URL", json={"prompt": prompt})
    return response.json()["answer"]

def execute_adb_click(widget_name):
    print(f"Executing ADB click on widget: {widget_name}")

def execute_adb_input(widget_name, input_text):
    print(f"Executing ADB input on widget {widget_name}: {input_text}")