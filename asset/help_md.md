# The float window for function state

The first line displays the status of the screenshot capture function:

- The left indicator S-M turns red to show it is currently monitoring the selected area.
- The right indicator S-C turns red if a screenshot has been taken.

The second line displays the status of the speech recognition function:

- The left indicator Mic turns red to show it is currently listening to microphone input.
- The right indicator Sys turns red if it is currently capturing system audio (WASAPI loopback); if the Sys indicator is gray, no system audio loopback device was found.


Right-click the floating window to control the start/stop screenshot and recognition.

# LLM service for voice recognition

*****
**>>>> Updated on 2026.6.30: System audio is now captured via WASAPI loopback — Stereo Mix is no longer required, and there is no feedback/echo risk. <<<<**

It automatically captures whatever is playing through the Windows **default output device**, using that device's native sample rate and channels (auto down-mixed to mono and resampled to 16 kHz for recognition). No manual setup is needed, and it adapts to different PCs automatically.

**>>> Note: make sure the meeting audio is actually playing through the system default output device; otherwise the captured stream will be silent. <<<**
*****

This feature uses the real-time speech recognition model provided by Alibaba Cloud: paraformer-realtime-v2, so an API key is required for connection.

Model page: https://bailian.console.aliyun.com/?tab=model#/model-market/detail/paraformer-realtime-v2

API Key application page: https://bailian.console.aliyun.com/?tab=model#/api-key

New users are entitled to a free trial of 10 hours. If you choose the paid version, the price is only 0.86 RMB per hour (0.12 USD)!

**>>>> Updated on 2026.1.6: Added a new position to fill in a custom real-time speech recognition model <<<<**

Available model list: https://bailian.console.aliyun.com/?tab=model#/model-market/all?capabilities=ASR

Once an API key has been entered, it will be automatically saved in a text file in the root directory of the program and will be automatically loaded when the program is opened again.

**>>>> Update on 2026.2.5: Added meeting minutes summary function! <<<<**

Click the "Minutes Summary" (Meeting Minutes) button on the main interface to pop up a new window. Fill in the API link, model name, and API URL, and you can start using it!

The pop-up window defaults to the folder where the data was last saved, but you can also browse and select another folder manually.

For example, the related configuration information for Deepseek can be seen at: https://api-docs.deepseek.com/zh-cn/

For others, you can refer to: https://docs.cherry-ai.com/pre-basic/providers/zi-ding-yi-fu-wu-shang

！！The API has not been well tested yet. Currently, it at least supports [deepseek](https://www.deepseek.com/), [Zhipu](https://open.bigmodel.cn/), and [Aliyun BaiLian](https://bailian.console.aliyun.com/cn-beijing/?spm=5176.29619931.J_SEsSjsNv72yRuRFS2VknO.6.74cd10d7VVqgml&tab=api#/api). Others should also be fine.

# Important

The computer will not enter sleep mode or turn off the screen during screen and audio monitoring.


# 功能状态的浮动窗口
第一行显示截图功能的状态：
- 左侧指示灯 S-M 变红，表示当前正在监控选定区域。
- 右侧指示灯 S-C 变红，表示已进行过截图操作。

第二行显示语音识别功能的状态：
- 左侧指示灯 Mic 变红，表示当前正在监听麦克风输入。
- 右侧指示灯 Sys 变红，表示当前正在捕获系统音频（WASAPI loopback）；若 Sys 指示灯为灰色，则表示未找到系统音频 loopback 设备。

右键点击浮动窗口，可以控制开始/停止截图、识别。

# 语音识别的LLM服务

*****
**>>>>2026.6.30更新：系统音频改为通过 WASAPI loopback 捕获——不再需要开启立体声混音，也不会产生啸叫。<<<<**

它会自动捕获 Windows **默认输出设备** 正在播放的声音，按设备原生采样率与声道采集（自动下混为单声道并重采样到 16 kHz 送入识别），无需任何手动设置，换到不同电脑也能自适应。

**>>> 注意：请确保会议声音是从系统默认输出设备播出的，否则捕获到的会是静音。<<<**
*****

本功能使用阿里云提供的实时语音识别模型：paraformer-realtime-v2，因此连接时需要API密钥。

模型页面：https://bailian.console.aliyun.com/?tab=model#/model-market/detail/paraformer-realtime-v2

申请API密钥页面：https://bailian.console.aliyun.com/?tab=model#/api-key

新用户享有10小时的免费试用。若选择付费版本，价格仅为每小时0.86人民币（0.12美元）！

**>>>>2026.1.6更新：新增一个位置可以填写自定义的实时语音识别模型<<<<**

可用的模型列表：https://bailian.console.aliyun.com/?tab=model#/model-market/all?capabilities=ASR

一旦输入了API密钥，它将自动保存在程序根目录下的一个配置文件中，并在下次打开程序时自动加载。

# 会议纪要整理的LLM服务

**>>>>2026.2.5更新：新增了会议纪要总结功能！<<<<**

主界面点击“Minutes Summary”（会议纪要）按钮，会弹出新的窗口，填写API链接、模型名称和API网址，即可使用！

弹出窗口默认使用刚刚保存数据的文件夹，也可以自行浏览选择。

例如，Deepseek的相关配置信息见：https://api-docs.deepseek.com/zh-cn/

其他可参考：https://docs.cherry-ai.com/pre-basic/providers/zi-ding-yi-fu-wu-shang

！！ API还没有很好的测试，目前至少支持[deepseek](https://www.deepseek.com/)、[智谱](https://open.bigmodel.cn/)、[阿里云百炼](https://bailian.console.aliyun.com/cn-beijing/?spm=5176.29619931.J_SEsSjsNv72yRuRFS2VknO.6.74cd10d7VVqgml&tab=api#/api)，其他的应该也没问题

# 重要

在进行屏幕和语音监测期间，电脑将不会进入睡眠和关闭屏幕。