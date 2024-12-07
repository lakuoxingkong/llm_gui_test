
import subprocess
import re

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