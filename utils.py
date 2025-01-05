import time
import os
import subprocess
import re
from openai import OpenAI
import os

# deepseek API Key
deepseek_key = ''
# input your key
gemini_key = ''

def getAllComponents(data_dict: dict):

    root = data_dict['hierarchy']

    queue = [root]
    res = []
    #
    node_cnt = 0
    while queue:
        currentNode = queue.pop(0)
        # 跳过包含systemui的node
        if ('@resource-id' in currentNode and 'com.android.systemui' in currentNode['@resource-id']) or (
                '@package' in currentNode and 'com.android.systemui' in currentNode['@package']):
            continue
        node_cnt += 1
        # 若非叶节点
        if 'node' in currentNode:
            # 若可点击
            if '@clickable' in currentNode and currentNode['@clickable'] == 'true':
                # 将子节点也记为clickable
                if type(currentNode['node']).__name__ == 'dict':
                    currentNode['node']['@clickable'] = 'true'
                else:
                    for e in currentNode['node']:
                        e['@clickable'] = 'true'
            # currentNode['node']可能是字典或列表。将子节点入队
            if type(currentNode['node']).__name__ == 'dict':
                queue.append(currentNode['node'])
            else:
                for e in currentNode['node']:
                    queue.append(e)
        else:
            res.append(currentNode)

    return res

def get_common_desc(e: dict):
    """
    :param e:
    :return:
    """
    text = e['@text']
    content = e['@content-desc']
    rid = e['@resource-id']
    bounds = e['@bounds']
    desc = ""
    if text != "":
        desc = text
    elif content != "":
        desc = content
    elif rid != "":
        desc = rid.split('/')[-1]
        desc = desc.replace('_', ' ')
    else:
        desc = ""
    return {"desc": desc, "bounds": bounds}


def rename_duplicate(alist):
    """
    对相同的desc重命名
    :param alist:
    :param print_result:
    :return:
    """
    new_list = [v + str(alist[:i].count(v) + 1) if alist.count(v) > 1 else v for i, v in enumerate(alist)]
    return new_list

def get_bounds(bounds):
    """
    将xml中的bounds属性字符串转换为int数组
    return: [左上x，左上y，右下x，右下y]
    """
    res = []
    bounds = bounds.split(',')
    res.append(bounds[0].replace('[', ''))
    mid = bounds[1].split('][')
    res.append(mid[0])
    res.append(mid[1])
    res.append(bounds[2].replace(']', ''))
    res = [int(e) for e in res]
    return res


def split_page(all_components: list):
    """
    :param components:
    :return: 2个component列表
    """
    size_str = subprocess.getoutput("adb shell wm size")
    size_str = size_str.split(' ')[-1]
    size_str = size_str.split('x')
    width = int(size_str[0])
    height = int(size_str[1])

    up_half = []
    down_half = []

    for e in all_components:
        bounds = e['@bounds']
        res = get_bounds(bounds)
        y = (res[1] + res[3]) / 2
        if y < height / 2:
            up_half.append(e)
        else:
            down_half.append(e)

    return up_half, down_half

def get_running_info():
    """
    """
    cmd = r"adb shell dumpsys activity activities | findstr mControlTarget=Window"
    res = subprocess.getoutput(cmd)
    real_res = res.split('\n')[0].strip()
    p1 = re.compile(r'[{](.*?)[}]', re.S)
    arr = re.findall(p1, real_res)
    final_ans = arr[0].split()[-1].split('/')
    if len(final_ans) < 2:
        return
    app_name = final_ans[0]
    activity_name = final_ans[1][len(app_name) + 1: -1]
    return {'app': app_name, 'activity': activity_name}

def click(text_name: str, all_components: list):
    """
    :param text_name:
    :param all_components:
    :return:
    """
    time.sleep(0.5)
    # global pic_index
    is_clicked = False
    for e_component in all_components:
        if e_component['@desc'] == text_name:
            bounds = e_component['@bounds']
            res = get_bounds(bounds)
            # screen_shot(pic_index, res)
            # pic_index += 1
            cmd = "adb shell input tap {x} {y}"
            cmd = cmd.replace('{x}', str((res[0] + res[2]) / 2)).replace('{y}', str((res[1] + res[3]) / 2))
            print("run command: {}".format(cmd))
            os.system(cmd)
            is_clicked = True
            break
    if is_clicked:
        print(text_name + " is clicked.")
    else:
        print(text_name + " is not found.")

def input_text(content: str, bounds):
    """
    """
    # global pic_index
    res = get_bounds(bounds)
    # screen_shot(pic_index, res)
    # pic_index += 1

    cmd = "adb shell input tap {x} {y}"

    cmd = cmd.replace('{x}', str((res[0] + res[2]) / 2)).replace('{y}', str((res[1] + res[3]) / 2))
    print("run command: {}".format(cmd))
    os.system(cmd)

    content = content.replace(' ', '\ ')

    cmd = "adb shell input text " + content
    print("run command: {}".format(cmd))
    os.system(cmd)


class Chat:
    def __init__(self):
        self.llm = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
        self.model_name = "deepseek-chat"
        self.messages = [
            {"role": "system",
             "content": """
Now that you are an automated testing program for Android software, \
what you have to do is test the functionality of the software as completely as possible \
and check for any problems. I will tell you the information of the current program interface \
by asking questions, and you will tell me the next step of the test by answering.

When you encounter components with similar names, you can look at them as the same category and test one or more of them. When you encounter many operation options, you tend to click on them from smallest to largest, and tend to click on the component with "menu button" in its name.

Now that you are an automated testing program for Android software, what you have to do is test the functionality of the software as completely as possible and check for any problems. I will tell you the information of the current program interface by asking questions, and you will tell me the next step of the test by answering.
             """},
            ]
        
    def send_message(self, message):
        self.messages.append({"role": "user", "content": message})
        response = self.llm.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            stream=False
        )
        self.messages.append(response.choices[0].message)
        return response.choices[0].message.content