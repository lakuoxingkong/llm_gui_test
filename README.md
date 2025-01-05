# 大模型引导的自动化安卓应用测试工具

本软件用于自动化测试安卓app的图形界面，基于论文Make LLM a Testing Expert: Bringing Human-like Interaction to
Mobile GUI Testing via Functionality-aware Decisions中的GPTDroid。虽然文中给出了源代码仓库链接，
但链接已失效。另外找到 https://github.com/testinging6/GPTDroid 也是该论文的实现，但与原文有差别
（如prompt与原文描述不一致），本软件在其基础上进行了修改。
## 演示视频
https://box.nju.edu.cn/f/3e1f211be808408d8870/

## 使用方法
#### Requirements
* Android emulator
* Android SDK
* Python 3.9
  * uiautomator2
  * google.generativeai

我们使用Google gemini-1.5-flash的API，因为它免费（每分钟最多15次请求）。需要科学上网。
需要您自行申请gemini的key，将key填入utils.py的gemini_key变量中。
gemini使用可参考https://blog.csdn.net/zwqjoy/article/details/135058668

我目前使用Android Studio自带的Android模拟器作为运行环境。创建默认的Android 15.0系统的虚拟手机。
在Android Studio中启动该手机，将.apk拖到手机位置以安装app。打开app，然后运行我们的代码

`python main.py`

即开始对该app的自动测试。
需要提前在main.py中手动输入appname（app的名称）和AndroidManifest_filepath（AndroidManifest.xml的路径）的值。

由于我们需要从AndroidManifest.xml中提取app信息，需要安装apktool工具用于反编译.apk文件。
apktool使用参考https://blog.csdn.net/shulianghan/article/details/121027522 ，
我们只需下载jar包后执行 `java -jar apktool_2.4.1.jar d demo.apk -o demo` 命令即可，
其中 d 后面是要反编译的
apk文件路径, -o后面是反编译结果的输出目录，我们只需要其中的AndroidManifest.xml，如本仓库中的
apk8_AndroidManifest.xml就是反编译8.apk得到的AndroidManifest.xml。

论文中使用了uiautomator这个python库用于提取GUI页面信息hierarchy.xml，但该库已多年未更新。
而uiautomator2是基于uiautomator写的另一个python库，该库近期有更新。
根据实验，uiautomator2在低版本Android（如Android7.0） 中无法正常使用，
在高版本Android（如Android 15.0）则正常。而uiautomator在Android7.0中正常使用，
在Android 15.0中不正常。目前我们选择了uiautomator2 + Android 15.0的环境。
另外需要注意，若在Android Studio使用Android7.0的虚拟机，需要自行打开开发者模式以打开usb调试。

本程序需要使用AndroidSDK的adb工具来实现与Android设备的交互。如果您安装Android Studio，同时
也会下载AndroidSDK，无需额外下载。该工具位于AndroidSDK安装目录的platform-tools目录中。

若您使用Windows，需要注意，在Android Studio的安装过程中，会自动将.android（虚拟机会放在里面）和
.gradle（gradle构建工具会放在里面）目录放在C盘的用户目录中。可以自行将这2个目录移动到非系统盘。
同时需要修改一些配置项，可参考网上教程。

---

## 补充说明

* 除了主分支的Gemini API，本项目还使用了deepseek的API作为替代，相关的改动可参考分支'openai'
* 本项目对"状态表示和验证机制"和"工作流管理机制"也尝试了实现，但性能较差，所以将其暂时放在了'extend'分支，具体的实现可查看该分支下的代码

接下来，基于extend分支，对系统进行详细的说明

### 系统特性

* 自动感知和理解测试场景
* 生成符合场景要求的测试操作
* 验证应用状态是否符合预期
* 实现完整的自动化测试工作流

### 代码结构

``` text
llm_gui_test/
├── main.py              # 主程序
├── state_validator.py   # 状态验证
├── workflow_manager.py  # 工作流管理
├── utils.py            # 工具函数
└── requirements.txt    # 依赖项
```

### 已完成功能

1. 测试场景感知与理解
    * 通过大模型理解测试场景目标
    * 实时分析待测应用状态
    * 理解应用状态与场景的关联
2. 基于场景的测试操作生成
    * 生成符合场景的GUI测试操作
    * 集成Appium等工具执行操作
3. 基于场景的应用状态验证
    * 验证测试操作的执行结果
    * 检查应用状态是否符合预期
4. 完整的自动化测试工作流
    * 状态偏离修正
    * 操作失败处理
    * 完整工作流实现
5. 交互界面
    * 基础的命令行输出

### 待改进功能

1. B/S架构的完整实现
2. 测试过程可视化
3. RAG增强的场景理解

### 运行环境及使用说明

与主体内容的“使用方法”基本一致，不过，extend分支使用的是deepseek的API，需要额外安装OpenAI的依赖，还需配置您自己的API密钥。

### 运行示例

见'运行输出示例.txt'和'演示视频2'

### 结果分析

#### 测试流程概述

测试系统成功执行了6个步骤的自动化测试，主要覆盖了以下功能点：

1. **添加记录功能** (步骤1-3)
   * 点击添加按钮
   * 输入数字1
   * 确认保存

2. **搜索功能** (步骤4-6)
   * 进入搜索界面
   * 尝试搜索"餐饮"
   * 尝试搜索"交通"

#### 成功完成的功能

1. **场景感知**
   * 正确识别当前页面状态
   * 准确理解可交互组件

2. **状态验证**
   * 每步操作后进行状态验证
   * 提供详细的验证结果报告

3. **工作流管理**
   * 实现了完整的测试工作流
   * 提供策略调整建议

#### 存在的问题

1. **输入文本异常**

    ``` sh
    Exception occurred while executing 'text':
    java.lang.NullPointerException
    ```

    * 在搜索功能测试中出现输入异常

2. **组件识别问题**

    * "Back"按钮识别失败

#### 整体评估

系统基本实现了场景感知的GUI自动化测试，具备一定的智能性，但在某些细节实现上还需完善。
