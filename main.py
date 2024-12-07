import uiautomator2 as u2
import json
import xmltodict
from utils import *
from pprint import pprint
import re
import xml.etree.ElementTree as ET

# TODO:自動提取app名
appname = 'booyah!'


def extract_app_info(appname):
    filepath = 'apk8_AndroidManifest.xml'
    tree = ET.parse(filepath)

    root = tree.getroot()

    app = root.find('application')

    activities = []

    for e in app.iter('activity'):
        if e.find('intent-filter') is not None:
            activities.append(e.attrib['{http://schemas.android.com/apk/res/android}name'].split('.')[-1].replace('Activity', ''))

    print(activities)

    # prompt = fewshot
    # prompt += 'Q: Here is an app named "{}", and all its activities are: '.format(appname)
    #
    # for e in activities:
    #     prompt += e + ", "
    #
    # prompt = prompt[:-2] + '. Please give the order of testing for these activities.'
    #
    # print('prompt: {}'.format(prompt))
    # res = getOutput(prompt)
    # print('res: {}'.format(res))
    # real_res = res[20: -1]
    # print('real res: {}'.format(real_res))
    # order_list = real_res.split(',')
    # for i in range(len(order_list)):
    #     order_list[i] = '{}_{}'.format(i + 1, order_list[i].strip())
    # print(order_list)

    jsondata = {
        "Global information attribute": [{
            "App name" : appname,
            "Activities": activities,
            # "Priority": order_list
        }]
    }

    print('json data:')
    pprint(jsondata)
    return jsondata


json_data = extract_app_info(appname)

d = u2.connect() # connect to device
print(d.info)
page_source = d.dump_hierarchy(compressed=True, pretty=True)
xml_file = open('hierarchy2.xml', 'w', encoding='utf-8')
xml_file.write(page_source)
xml_file.close()
xml_file = open('hierarchy2.xml', 'r', encoding='utf-8')
data_dict = xmltodict.parse(xml_file.read())
# data_str = json.dumps(data_dict)
# json_file = open(save_path + 'hierarchy.json', 'w', encoding='utf-8')
# json_file.write(data_str)
# json_file.close()

all_components = getAllComponents(data_dict)

running_info = get_running_info()
# ActivityName
activity_name = running_info['activity'].replace('.', ' ').split(' ')[-1].replace('Activit', '')
print("activity_name: {}".format(activity_name))

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

# searching for editable components
edit_list = []
for e_component in components_list:
    if '@class' in e_component and (e_component['@class'] == 'android.widget.EditText' or
                                    e_component['@class'] == 'android.widget.AutoCompleteTextView'):
        edit_list.append(e_component)

print("--- There are describable components: ---")
for e in components_list:
    print(e)
print("----------------------------------------")

print("--- There are clickable components: ---")
for e in clickable_list:
    print(e)
print("----------------------------------------")

print("--- There are editable components: ---")
for e in edit_list:
    print(e)
print("----------------------------------------")

up_half, down_half = split_page(components_list)

up_half = [e["@desc"] for e in up_half]
down_half = [e["@desc"] for e in down_half]

print("up half: {}".format(up_half))
print("down half: {}".format(down_half))

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
pprint(widget_list)


json_data["Page information attribute"] = [{
    "ActivityName": activity_name,
    "Widgets": [e["@desc"] for e in components_list],
    "Layouts": [
        {
            "Upper half": up_half,
            "Lower half": down_half
        }
    ]
    # "VisitTime": "1",
    # "Duplicate": "0"
}]
json_data["Widget information attribute"] = [{}]
for i, e in enumerate(widget_list):
    json_data["Widget information attribute"][0]["Widget_{}".format(str(i + 1))] = [e]

print("json data:")
pprint(json_data)

# jsonstr = json.dumps(jsondata)
# f = open('./json/{}-step{}.json'.format(appname, str(step + 1)), 'w')
# f.write(jsonstr)
# f.close()

prompt = 'We want to test the "{}" App. It has the following activities, including '.format(appname)
for e in json_data["Global information attribute"][0]["Activities"]:
    prompt += '"{}", '.format(e)
prompt = prompt[:-2]
# prompt += '.\nThe recommended test sequence is: '
# for e in json_data["Global information attribute"][0]["Priority"]:
#     prompt += '"{}", '.format(e)
# prompt = prompt[:-2]
prompt += '.\nThe current page is "{}"'.format(activity_name)
# prompt += 'The number of expoloration recorded on the current page is {}.\n'.format(json_data["Page information attribute"][0]["VisitTime"])
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
        prompt += '{} is {}'.format(w['widgetT'], w['WidgetC'])
    elif 'widgetID' in w:
        prompt += '{} is {}'.format(w['widgetID'], w['WidgetC'])
    if w['WidgetAct'] == 'Click':
        prompt += ' which can be clicked'
    prompt += '. '

if len(edit_list) == 0:
    prompt += '\nWhat operation is required? (<Operation>[click / double-click / long press / scroll]+<Widget Name>)'
else:
    prompt += '\nPlease generate the input text in sequence, and the operation after input. (<Widget name>+<Input Content>, ...) and provided (<Operation[click]>+<Widget name>)'
# prompt += "Now we can do these:\n"
# opt_id = 1
# for e in clickable_list:
#     prompt += '{}. click "{}"\n'.format(str(opt_id), e["desc"])
#     opt_id += 1
# prompt += "{}. return to previous page\n".format(str(opt_id))
# prompt += "What do you choose to do? Please answer directly with one of the options. \n"
print(prompt)
