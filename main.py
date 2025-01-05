import uiautomator2 as u2
import json
import xmltodict
from utils import *
from pprint import pprint
import re
import xml.etree.ElementTree as ET
from state_validator import StateValidator
from workflow_manager import TestWorkflowManager

# TODO:自動提取app名
appname = 'cashbook'
AndroidManifest_filepath = 'cashbook_AndroidManifest.xml'

def extract_app_info(appname):
    filepath = AndroidManifest_filepath
    tree = ET.parse(filepath)
    root = tree.getroot()
    app = root.find('application')

    activities = []
    for e in app.iter('activity'):
        if e.find('intent-filter') is not None:
            activities.append(e.attrib['{http://schemas.android.com/apk/res/android}name'].split('.')[-1].replace('Activity', ''))
    print(activities)

    jsondata = {
        "Global information attribute": [{
            "App name" : appname,
            "Activities": activities,
        }]
    }
    print('json data:')
    pprint(jsondata)
    return jsondata

def get_page_hierarchy():
    d = u2.connect() # connect to device
    # print(d.info)
    page_source = d.dump_hierarchy(compressed=True, pretty=True)
    xml_file = open('hierarchy.xml', 'w', encoding='utf-8')
    xml_file.write(page_source)
    xml_file.close()
    # from uiautomator import device as d
    # d.dump("hierarchy.xml")
    xml_file = open('hierarchy.xml', 'r', encoding='utf-8')
    data_dict = xmltodict.parse(xml_file.read())
    return data_dict


chat = Chat()
json_data = extract_app_info(appname)
def main(step):
    workflow_manager = TestWorkflowManager(chat)
    
    try:
        data_dict = get_page_hierarchy()
        all_components = getAllComponents(data_dict)
        running_info = get_running_info()
        activity_name = running_info['activity'].replace('.', ' ').split(' ')[-1].replace('Activit', '')
        
        # 检查是否需要探索当前状态
        if not workflow_manager.should_explore_state(activity_name, all_components):
            print(f"状态 {activity_name} 已探索过，跳过")
            return

        # searching for describable components
        components_list = []
        for e_component in all_components:
            info = get_common_desc(e_component)
            desc = info['desc']
            if desc != "":
                e_component['@desc'] = desc
                components_list.append(e_component)

        origin_list = [e["@desc"] for e in components_list]
        renamed_list = rename_duplicate(origin_list)
        for i, e in enumerate(renamed_list):
            components_list[i]["@desc"] = e

        # searching for clickable components
        clickable_list = []
        for e_component in components_list:
            if e_component['@clickable'] == 'true':
                info = {"desc": e_component["@desc"], "bounds": e_component["@bounds"]}
                clickable_list.append(info)
        if len(clickable_list) == 0:
            print('现在没有可点击的widget。为防止手机卡死，睡眠30秒')
            time.sleep(30)
            return

        # searching for editable components
        edit_list = []
        for e_component in components_list:
            if '@class' in e_component and (e_component['@class'] == 'android.widget.EditText' or
                                            e_component['@class'] == 'android.widget.AutoCompleteTextView'):
                edit_list.append(e_component)

        up_half, down_half = split_page(components_list)

        up_half = [e["@desc"] for e in up_half]
        down_half = [e["@desc"] for e in down_half]

        # WidgetC WidgetID/WidgetT WidgetAct WidgetV--全部为0，在干什么？
        widget_list = []
        for e in components_list:
            temp = {}
            #
            temp["WidgetC"] = e["@class"].split(".")[-1]
            #
            if e["@text"] == "" and e["@content-desc"] == "":
                temp["widgetID"] = e["@desc"]
            else:
                temp["widgetT"] = e["@desc"]
            #
            temp["WidgetAct"] = "none"
            if "@clickable" in e and e["@clickable"] == "true":
                temp["WidgetAct"] = "Click"
            #
            temp["WidgetV"] = "0"
            widget_list.append(temp)

        json_data["Page information attribute"] = [{
            "ActivityName": activity_name,
            "Widgets": [e["@desc"] for e in components_list],
            "Layouts": [
                {
                    "Upper half": up_half,
                    "Lower half": down_half
                }
            ]
        }]
        json_data["Widget information attribute"] = [{}]
        for i, e in enumerate(widget_list):
            json_data["Widget information attribute"][0]["Widget_{}".format(str(i + 1))] = [e]

        if step == 0:
            prompt = 'We want to test the "{}" App. It has the following activities, including '.format(appname)
            for e in json_data["Global information attribute"][0]["Activities"]:
                prompt += '"{}", '.format(e)
            prompt = prompt[:-2] + '.\n'
        else:
            prompt= 'We successfully did the above operation. '
        prompt += 'The current page is "{}"'.format(activity_name)
        prompt += ", it has "
        for e_component in components_list:
            prompt += '"{}", '.format(e_component["@desc"])
        prompt = prompt[:-2]
        prompt += '. The upper part of the app is "'
        for e in up_half:
            prompt += '{}, '.format(e)
        prompt = prompt[:-2]
        prompt += '", the lower part of the app is "'
        for e in down_half:
            prompt += '{}, '.format(e)
        prompt = prompt[:-2]
        # Widget information. TODO: nearby widgets.
        prompt += '".\n'
        for w in widget_list:
            if 'widgetT' in w:
                prompt += '"{}" is {}'.format(w['widgetT'], w['WidgetC'])
            elif 'widgetID' in w:
                prompt += '"{}" is {}'.format(w['widgetID'], w['WidgetC'])
            if w['WidgetAct'] == 'Click':
                prompt += ' which can be clicked'
            prompt += '. '

        if len(edit_list) == 0:
            prompt += '''\nWhat operation is required? (<Operation>[click / double-click / long press / scroll]+<Widget Name>)
        Answer in the following format. Only this. Only one operation.
        【Operation: "Click". Widget: "ADD INCOME".】'''
        else:
            prompt += '''\nPlease generate the input text in sequence, and the operation after input. (<Widget name>+<Input Content>, ...) and provided (<Operation[click]>+<Widget name>)
        Answer in the following format. Only this. Generate inupt for all editable widgets and then make only one operation.
        【Widget: "Price". Input: "3500". Widget: "Title". Input: "salary". Widget: "Category". Input: "personal". Operation: "Click". Widget: "Submit".】'''

        while True:
            try:
                response = chat.send_message(prompt)
                break
            except:
                print('llm使用次数达到限制，等待60秒')
                time.sleep(60)
        llm_answer = response
        print('llm_answer')
        print(llm_answer)

        # TODO: 异常处理不完善。下面这一段正常运行的前提是，llm_answer的格式正常
        # 提取所有 Widget 和对应的 Input
        widget_input_pattern = r'Widget: "([^"]+)".*?Input: "([^"]+)"'
        widget_input_matches = re.findall(widget_input_pattern, llm_answer)

        # 提取 Operation 和其后的 Widget
        operation_widget_pattern = r'Operation: "([^"]+)".*?Widget: "([^"]+)"'
        operation_match = re.search(operation_widget_pattern, llm_answer)

        # 做Input操作
        if widget_input_matches:
            for widget, input_value in widget_input_matches:
                # print(f"Widget: {widget}, Input: {input_value}")
                for e in edit_list:
                    if e['@desc'] == widget:
                        input_text(input_value, e['@bounds'])
        else:
            print("没有找到匹配的 Widget 和 Input.")

        validator = StateValidator(chat)
        
        # 在执行操作前记录预期状态
        if operation_match:
            operation_value = operation_match.group(1)
            widget_after_operation = operation_match.group(2)
            
            # 让LLM预测操作后的预期状态
            prediction_prompt = f"""
预测执行 {operation_value} 操作在 {widget_after_operation} 上后的预期状态:
1. 界面应该显示哪些组件?
2. 输入框中应该有什么值?
3. 应该跳转到什么页面吗?
"""
            expected_state = chat.send_message(prediction_prompt)
            validator.record_expected_state(f"{operation_value} {widget_after_operation}", expected_state)
            
            # 执行操作
            if operation_value.lower() == 'click':
                click(widget_after_operation, components_list)
                
            # 等待界面稳定
            time.sleep(1)
            
            # 获取新状态并验证
            new_data_dict = get_page_hierarchy()
            new_components = getAllComponents(new_data_dict)
            new_running_info = get_running_info()
            new_activity = new_running_info['activity'].replace('.', ' ').split(' ')[-1].replace('Activit', '')
            
            validator.capture_current_state(new_components, new_activity)
            validation_result = validator.verify_state(f"{operation_value} {widget_after_operation}")
            print("状态验证结果:")
            print(validation_result)
            
            # 执行测试操作前的策略调整
            if step % 5 == 0:  # 每5步调整一次策略
                strategy = workflow_manager.adjust_test_strategy()
                print("策略调整建议:", strategy)
            
            # 执行测试操作
            try:
                if operation_match:
                    operation_value = operation_match.group(1)
                    widget_after_operation = operation_match.group(2)
                    
                    if operation_value.lower() == 'click':
                        click(widget_after_operation, components_list)
                        
                    # 验证操作结果
                    validation_result = validator.verify_state(f"{operation_value} {widget_after_operation}")
                    if "状态验证失败" in validation_result:
                        workflow_manager.record_failed_operation(
                            f"{operation_value} {widget_after_operation}",
                            validation_result
                        )
                        recovery_action = workflow_manager.get_recovery_action(validation_result)
                        print("恢复建议:", recovery_action)
                        
            except Exception as e:
                print(f"操作执行异常: {str(e)}")
                workflow_manager.record_failed_operation(
                    f"{operation_value} {widget_after_operation}",
                    str(e)
                )
                recovery_action = workflow_manager.get_recovery_action(str(e))
                print("异常恢复建议:", recovery_action)
                
            # 更新测试进度
            workflow_manager.test_progress[step] = {
                'activity': activity_name,
                'operation': f"{operation_value} {widget_after_operation}",
                'result': validation_result
            }
                
        else:
            print("没有找到匹配的 Operation 和 Widget.")
            
    except Exception as e:
        print(f"工作流执行异常: {str(e)}")
        recovery_action = workflow_manager.get_recovery_action(str(e))
        print("工作流恢复建议:", recovery_action)

if __name__ == '__main__':
    for step in range(25):
        print(f'step{step + 1} begins')
        main(step)
        print(f'step{step + 1} ends')