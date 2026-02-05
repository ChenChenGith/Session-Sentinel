# Repositories url: https://github.com/ChenChenGith/Video_PPT_capture

# version: 0.1.0
# license: MIT

from PIL import ImageGrab, ImageChops, ImageStat, Image, ImageTk
import time
import tkinter as tk
from tkinter import filedialog
import sys, os
from screeninfo import get_monitors
import multiprocessing
import json
import requests

from dashscope.audio.asr import RecognitionCallback, RecognitionResult, Recognition
import dashscope
import pyaudio

from http import HTTPStatus

import webbrowser
import ctypes

def get_all_display_info():
    x, y = [], []
    for m in get_monitors():
        x.append(m.x)
        x.append(m.x + m.width)
        y.append(m.y)
        y.append(m.y + m.height)
    
    return max(x) - min(x), max(y) - min(y), min(x), min(y)

def find_stereo_mix_device(mic):
    keyword_list = ["stereo mix", "立体声混音"]
    for i in range(mic.get_device_count()):
        info = mic.get_device_info_by_index(i)
        name = info.get('name', '').lower()
        if info.get('maxInputChannels', 0) > 0:
            for kw in keyword_list:
                if kw in name:
                    # 尝试打开设备，能打开才算可用
                    try:
                        test_stream = mic.open(format=pyaudio.paInt16,
                                              channels=1,
                                              rate=16000,
                                              input=True,
                                              input_device_index=i)
                        test_stream.close()
                        return i
                    except Exception as e:
                        continue
    return None

class Capture_window_select(object):
    def __init__(self, capture_window=None):
        self.window = tk.Tk()
        self.window.overrideredirect(True)         # 隐藏窗口的标题栏
        self.window.attributes("-alpha", 0.5)      # 窗口透明度10%
        
        self.width, self.height, self.x, self.y = get_all_display_info()
        
        # self.width = self.window.winfo_screenwidth()
        # self.height = self.window.winfo_screenheight()
        self.window.geometry("{0}x{1}+{2}+{3}".format(self.width, self.height, self.x, self.y))

        self.window.bind('<Escape>', self.exit_1)
        self.window.bind('<Return>', self.exit_2)
        self.window.bind("<Button-1>", self.selection_start)  # 鼠标左键点击->显示子窗口 
        self.window.bind("<ButtonRelease-1>", self.selection_end) # 鼠标左键释放->记录最后光标的位置
        self.window.bind("<B1-Motion>", self.change_selection)   # 鼠标左键移动->显示当前光标位置

        self.canvas = tk.Canvas(self.window, width=self.width, height=self.height)
        self.canvas.pack()

        self.remember = None
        if capture_window != None:
            self.remember = capture_window
        else:
            self.remember = 0, 0, self.width, self.height

        self.canvas.create_text(self.width - 500, self.height - 500, text=f"Esc: Full-screen\nLeft click and move: select capture region\nEnter: Confirm selection", fill="red", tags="info", font=("Arial", 30))

        self.window.focus_force()
        self.window.mainloop()

    def exit_1(self, event):
        self.window.destroy()
        self.window.quit()

    def exit_2(self, event):
        try:
            self.remember = [self.start_x, self.start_y, self.end_x, self.end_y]
        except:
            pass
        self.window.destroy()
        self.window.quit()
        
    def rel2abs(self, x, y):
        return x + self.x, y + self.y
    
    def selection_start(self, event):
        self.canvas.delete("rect", "text")
        self.win_start_x = event.x
        self.win_start_y = event.y
        self.rect = self.canvas.create_rectangle(self.win_start_x, self.win_start_y, self.win_start_x, self.win_start_y, outline='red', width=2, tags="rect", dash=(4, 4))
        
        self.start_x, self.start_y = self.rel2abs(event.x, event.y)
        
        self.canvas.create_text(self.win_start_x + 35, self.win_start_y + 10, text=f"({self.start_x}, {self.start_y})", fill="red", tags="text")
    
    def selection_end(self, event):
        self.win_end_x = event.x
        self.win_end_y = event.y
        self.end_x, self.end_y = self.rel2abs(event.x, event.y)
        self.canvas.create_text(self.win_end_x - 90, self.win_end_y - 25, text=f"({self.end_x}, {self.end_y})({self.end_x-self.start_x}X{self.end_y-self.start_y})", fill="red", tags="text")
        self.canvas.create_text(self.win_end_x - 100, self.win_end_y - 10, text="Press Enter to confirm selection", fill="red", tags="text")

    def change_selection(self, event):
        self.canvas.coords(self.rect, self.win_start_x, self.win_start_y, event.x, event.y)
    
    def get_capture_window_coor(self):
        x1, y1, x2, y2 = self.remember
        return [
            min(x1, x2),
            min(y1, y2),
            max(x1, x2),
            max(y1, y2)
        ]

def get_resource_path(relative_path):
    # If running as a PyInstaller exe, use exe directory for resources
    if hasattr(sys, 'frozen'):
        # sys.executable is the path to the exe
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, relative_path)
    elif hasattr(sys, "_MEIPASS"):
        # For onefile mode, _MEIPASS is the temp dir for bundled resources
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # For normal script, use current working directory
        return os.path.join(os.path.abspath("."), relative_path)

def get_resource_ico_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 配置管理函数
def load_config():
    """加载配置文件"""
    config_file = get_resource_path("config.json")
    default_config = {
        "dashscope": {
            "api_key": "",
            "model": "fun-asr-realtime-2025-11-07"
        },
        "llm": {
            "api_url": "https://api.deepseek.com",
            "api_key": "",
            "model": "deepseek-chat"
        },
        "prompt": {
            "no_image": """请将以下会议录音内容整理成Markdown格式的会议纪要。

要求：
1. 提取会议主题、时间、参与者等基本信息
2. 总结会议的主要讨论内容，按条目列出
3. 列出关键决策和行动项
4. 使用清晰的Markdown格式，包括标题、列表等

会议录音内容：
{asr_content}
""",
            "with_image": """请将以下会议录音内容整理成Markdown格式的会议纪要。
会议中共有{image_count}张PPT截图，请按照截图出现的时间顺序，为每张截图编写对应的主旨摘要。
截图标记格式为：'[SCREENSHOT: 文件名]'，请根据截图标记将录音内容分段。
输出格式要求：每张截图显示后，紧接对应的主旨摘要，截图要采用Markdown图片语法来引入。

要求：
1. 提取会议主题、时间、参与者等基本信息
2. 总结会议的主要讨论内容，按条目列出
3. 列出关键决策和行动项
4. 使用清晰的Markdown格式，包括标题、列表等

会议录音内容：
{asr_content}

可用的截图文件列表：
{image_list}

请输出Markdown格式的会议纪要。"""
        }
    }
    # 如果配置文件不存在，创建默认配置文件
    if not os.path.exists(config_file):
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    # 加载配置文件
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                # 合并默认配置和加载的配置
                for key in default_config:
                    if key in loaded_config:
                        default_config[key].update(loaded_config[key])
        except Exception:
            pass
    return default_config

def save_config(config):
    """保存配置文件"""
    config_file = get_resource_path("config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False) 

# Real-time speech recognition callback
class Callback(RecognitionCallback):
    def __init__(self, log_file, text_queue, stereo_mix_index=None, voice_source="stereo mix"):
        super().__init__()
        self.log_file = log_file
        self.text_queue = text_queue
        self.mic = None
        self.stream = None
        self.voice_source = voice_source
        self.stereo_mix_index = stereo_mix_index

    def on_open(self) -> None:
        self.text_queue.put(f"{self.time_str}: Speech recognition started, using {self.voice_source}.\n")
        self.mic = pyaudio.PyAudio()
        if self.voice_source == "stereo mix":            
            self.stream = self.mic.open(format=pyaudio.paInt16,
                                        channels=1,
                                        rate=16000,
                                        input=True,
                                        input_device_index=self.stereo_mix_index)
        elif self.voice_source == "mic":
            self.stream = self.mic.open(format=pyaudio.paInt16,
                                        channels=1,
                                        rate=16000,
                                        input=True)

    def on_close(self) -> None:
        self.text_queue.put(f"{self.time_str}: Speech recognition from source [{self.voice_source}] stopped.\n")
        self.stream.stop_stream()
        self.stream.close()
        self.mic.terminate()
        self.stream = None
        self.mic = None

    def on_complete(self) -> None:
        self.text_queue.put(f"\n{self.time_str}: RecognitionCallback completed.\n")

    def on_error(self, message) -> None:
        self.text_queue.put(f"{self.time_str}: RecognitionCallback error: {message.message}\n")
        # Stop and close the audio stream if it is running
        try:
            if self.stream.active:
                self.stream.stop()
                self.stream.close()
        except Exception as e:
            pass

    def on_event(self, result: RecognitionResult) -> None:
        sentence = result.get_sentence()
        # 只在句子结束时输出和累加，避免重复
        if RecognitionResult.is_sentence_end(sentence) and 'text' in sentence:
            self.text_queue.put(f"{self.time_str}: text from {self.voice_source}: {sentence['text']}\n")
            # 实时写入日志文件
            if self.log_file:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{self.time_str}: text from {self.voice_source}: {sentence['text']}\n")

    @property
    def time_str(self):
        return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def run_asr_process(log_filename, text_queue, apikey, model, stereo_mix_index, source="stereo mix"):
    dashscope.api_key = apikey
    callback = Callback(log_file=log_filename, text_queue=text_queue, stereo_mix_index=stereo_mix_index, voice_source=source)
    sample_rate = 16000  # 采样率
    format_pcm = 'pcm'  # 音频数据格式
    block_size = 3200  # 每次读取的帧数
    recognition = Recognition(
                model=model,
                format=format_pcm,
                sample_rate=sample_rate,
                semantic_punctuation_enabled=False,
                callback=callback)
    recognition.start()
    while True:
        if callback.stream:
            data = callback.stream.read(block_size, exception_on_overflow=False)
            recognition.send_audio_frame(data)
        else:
            break
    recognition.stop()

def set_system_sleep_state(state: bool, text_log: tk.Text):
    if state:
        # 设置系统不休眠
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
            text_log.insert(tk.END, "System sleep state set to: Not Sleep\n")
            return True
        except Exception as e:
            return False
    else:
        # 恢复系统休眠设置
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            text_log.insert(tk.END, "System sleep state set to: Sleep\n")
            return False
        except Exception as e:
            return True

class ScreenCapture(object):
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PESRT (PPT Extractor and Speech Recognition Tool. CC:ChenChenGith@github)")
        self.win_width, self.win_height = int(min(self.root.winfo_screenwidth()/1.8, 900)), int(min(self.root.winfo_screenheight(), 800))
        self.root.geometry("{0}x{1}+0+0".format(self.win_width, self.win_height))
        self.root.iconbitmap(get_resource_ico_path("asset/ycy.ico"))

        # 主frame，分为左侧信息区和右侧设置区
        self.main_frame = tk.Frame(self.root)
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # 左侧信息区
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.place(relx=0.02, rely=0.03, relwidth=0.68, relheight=0.94)
        # 上：截图信息
        tk.Label(self.left_frame, text="Screen Capture Info", anchor="w", font=("Arial", 11, "bold")).pack(fill="x")
        self.text_info = tk.Text(self.left_frame, height=18)
        self.text_info.pack(fill="x", expand=False)
        # 中：语音识别信息
        tk.Label(self.left_frame, text="Speech Recognition Info", anchor="w", font=("Arial", 11, "bold")).pack(fill="x", pady=(10,0))
        self.text_asr = tk.Text(self.left_frame, height=18)
        self.text_asr.pack(fill="both", expand=True)
        # 下：系统日志信息
        tk.Label(self.left_frame, text="System Log Info", anchor="w", font=("Arial", 11, "bold")).pack(fill="x", pady=(10,0))
        self.text_log = tk.Text(self.left_frame, height=8)
        self.text_log.pack(fill="both", expand=True)


        # 右侧设置区
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.place(relx=0.71, rely=0.03, relwidth=0.28, relheight=0.94)

        # 上：截图设置
        self.frame_cap = tk.LabelFrame(self.right_frame, text="Screen Capture Settings", font=("Arial", 10, "bold"))
        self.frame_cap.pack(fill="x", padx=2, pady=2)
        tk.Label(self.frame_cap, text="Check Interval (s)").grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        self.ety_capture_interval = tk.Entry(self.frame_cap, justify="center", width=6)
        self.ety_capture_interval.insert(0, "5")
        self.ety_capture_interval.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        self.scb_sensitivity = tk.Scale(self.frame_cap, from_=0, to=20, orient="horizontal", label="Sensitivity (0=High)", resolution=1, length=100)
        self.scb_sensitivity.set(2)
        self.scb_sensitivity.grid(row=1, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
        self.btn_window_config = tk.Button(self.frame_cap, text="Capture Window Selection", command=self.get_capture_window)
        self.btn_window_config.grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
        tk.Label(self.frame_cap, text="Capt. Win. Info:", fg='gray').grid(row=3, column=0, sticky="ew", padx=2, pady=2)
        self.label_capture_window = tk.Label(self.frame_cap, text="None", fg="gray")
        self.label_capture_window.grid(row=3, column=1, sticky="ew", padx=2, pady=2)
        self.btn_start = tk.Button(self.frame_cap, text="Start Capture", command=self.start_capture, state="disabled")
        self.btn_start.grid(row=6, column=0, sticky="ew", padx=2, pady=2)
        self.btn_stop = tk.Button(self.frame_cap, text="Stop Capture", command=self.stop_capture, state="disabled")
        self.btn_stop.grid(row=6, column=1, sticky="ew", padx=2, pady=2)
        self.frame_cap.columnconfigure(0, weight=1)
        self.frame_cap.columnconfigure(1, weight=1)

        # 下：语音识别设置
        self.frame_asr = tk.LabelFrame(self.right_frame, text="Speech Recognition Settings", font=("Arial", 10, "bold"))
        self.frame_asr.pack(fill="x", padx=2, pady=(5,2))
        tk.Label(self.frame_asr, text="Model").grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        self.ety_model = tk.Entry(self.frame_asr, width=18)
        self.ety_model.insert(0, "fun-asr-realtime-2025-11-07")
        self.ety_model.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        tk.Label(self.frame_asr, text="dashscope API Key").grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        self.ety_api_key = tk.Entry(self.frame_asr, show="*", width=18)
        self.ety_api_key.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        self.btn_use_input_api = tk.Button(self.frame_asr, text="Update Model&Key to config.json", command=self.use_input_api)
        self.btn_use_input_api.grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
        self.btn_asr_start = tk.Button(self.frame_asr, text="Start ASR", command=self.start_asr, state="normal")
        self.btn_asr_start.grid(row=4, column=0, sticky="ew", padx=2, pady=2)
        self.btn_asr_stop = tk.Button(self.frame_asr, text="Stop ASR", command=self.stop_asr, state="disabled")
        self.btn_asr_stop.grid(row=4, column=1, sticky="ew", padx=2, pady=2)
        # 两个勾选框分别选择是否开启麦克风和立体声混音监听，默认都勾选        
        self.stereo_mix_index = None
        self._check_stereo_mix()
        self.use_microphone = tk.BooleanVar(value=True)
        self.use_stereo_mix = tk.BooleanVar(value=True if self.stereo_mix_index else False)
        self.check_microphone = tk.Checkbutton(self.frame_asr, text="Microphone", variable=self.use_microphone, command=self._swtch_btn_asr_start)
        self.check_microphone.grid(row=3, column=0, sticky="ew", padx=2, pady=2)
        self.check_stereo_mix = tk.Checkbutton(self.frame_asr, text="Stereo Mix", variable=self.use_stereo_mix, state="normal" if self.stereo_mix_index else "disabled", command=self._swtch_btn_asr_start)
        self.check_stereo_mix.grid(row=3, column=1, sticky="ew", padx=2, pady=2)

        self.frame_asr.columnconfigure(0, weight=1)
        self.frame_asr.columnconfigure(1, weight=1)


        # 控制面板：一键启动/停止
        self.frame_ctrl = tk.LabelFrame(self.right_frame, text="Control Panel", font=("Arial", 10, "bold"))
        self.frame_ctrl.pack(fill="x", padx=2, pady=(5,2))
        self.btn_all_start = tk.Button(self.frame_ctrl, text="Start All", command=self.start_all, state="normal")
        self.btn_all_start.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        self.btn_all_stop = tk.Button(self.frame_ctrl, text="Stop All", command=self.stop_all, state="disabled")
        self.btn_all_stop.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        self.frame_ctrl.columnconfigure(0, weight=1)
        self.frame_ctrl.columnconfigure(1, weight=1)

        # 日志保存路径
        self.frame_save_path = tk.LabelFrame(self.right_frame, text="Log Save Path", font=("Arial", 10, "bold"))
        self.frame_save_path.pack(fill="x", padx=2, pady=(5,2))
        # 两行布局：第一行为标签和路径，第二行为按钮
        tk.Label(self.frame_save_path, text=f"Last\nSaved", fg='gray').grid(row=0, column=0, sticky="w", padx=2, pady=2)
        self.label_save_path = tk.Label(self.frame_save_path, fg="gray", bd=0, text="None", anchor="w", wraplength=120)
        self.label_save_path.grid(row=0, column=1, columnspan=2, sticky="ew", padx=2, pady=2)
        self.btn_save_path_open = tk.Button(self.frame_save_path, text="Open Folder", command=self.open_save_path, state="normal")
        self.btn_save_path_open.grid(row=1, column=0, columnspan=3, sticky="ew", padx=3, pady=2)
        self.frame_save_path.columnconfigure(1, weight=1)
        self.frame_save_path.columnconfigure(2, weight=0)

        # Minutes Summary按钮
        self.btn_minutes_summary = tk.Button(self.right_frame, text="Minutes Summary", command=self.open_minutes_summary, bg="green", fg="white")
        self.btn_minutes_summary.pack(fill="x", padx=2, pady=5)

        # add a help button
        self.btn_help = tk.Button(self.right_frame, text="Help", command=self.show_help)
        self.btn_help.pack(fill="x", padx=2, pady=5)

        btn_github = tk.Button(self.right_frame, text="Visit GitHub", command=self.open_github, bg="black", fg="white")
        btn_github.pack(padx=2, pady=5)

        # 退出按钮
        self.btn_sys_out = tk.Button(self.right_frame, text="Exit", command=self.sys_out)
        self.btn_sys_out.pack(side="bottom", fill="x", padx=2, pady=5)

        # 关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 是否显示浮动窗口复选框
        self.is_show_state_window_var = tk.BooleanVar()
        self.is_show_state_window = tk.Checkbutton(self.right_frame, text="Show State Window", command=self.show_state_window, variable=self.is_show_state_window_var)
        self.is_show_state_window.select()
        self.is_show_state_window.pack(side="bottom", fill="x", padx=2, pady=2)

        self.sensitivity = None
        self.is_capturing = False
        self.is_speech_recognizing = False
        self.is_asr_queue_checking = False
        self.is_setting_sys_not_sleep = False
        self.apikey = None
        self.model = None
        self.capture_window = None
        self.save_path = None
        self.log_filename = None
        self.im = None
        self.mouse_x, self.mouse_y = 0, 0

        self.asr_queue = multiprocessing.Queue()

        self.monitoring_countdown = 0

        # 加载配置到文本框
        self._load_config_to_ui()

        self.__init_state_window()
        self.root.mainloop()
    
    def _load_config_to_ui(self):
        """加载配置到UI文本框"""
        config = load_config()
        # 加载 ASR API Key
        dashscope_key = config.get("dashscope", {}).get("api_key", "")
        if dashscope_key:
            self.apikey = dashscope_key
            self.ety_api_key.delete(0, "end")
            self.ety_api_key.insert(0, self.apikey)
        # 加载 ASR Model
        dashscope_model = config.get("dashscope", {}).get("model", "")
        if dashscope_model:
            self.ety_model.delete(0, "end")
            self.ety_model.insert(0, dashscope_model)

    def _text_log_show(self, msg, color=None):
        if color:
            self.text_log.insert("end", msg, color)
            self.text_log.tag_config(color, foreground=color)
        else:
            self.text_log.insert("end", msg)
        self.text_log.see("end")

    def start_all(self):
        # 启动截图和语音识别
        do_not_prapare = False
        if self.capture_window is None:
            self._text_log_show(f"{self.time_str}: Please select capture window first!\n", "red")
            do_not_prapare = True
        if not self._check_has_input_api_model():
            do_not_prapare = True
        if not self._check_api_key_valid():
            do_not_prapare = True
        if do_not_prapare:
            return
        
        if not self.is_setting_sys_not_sleep:
            self.is_setting_sys_not_sleep = set_system_sleep_state(True, self.text_log)
        if self.btn_asr_start['state'] == 'normal':
            self.start_asr()
        if self.btn_start['state'] == 'normal':
            self.start_capture()
        self.btn_all_start['state'] = 'disabled'
        self.btn_all_stop['state'] = 'normal'


    def stop_all(self):
        # 停止截图和语音识别（仅UI按钮状态切换，功能后续实现）
        if self.btn_stop['state'] == 'normal':
            self.stop_capture()
        if self.btn_asr_stop['state'] == 'normal':
            self.stop_asr()
        self.btn_all_start['state'] = 'normal'
        self.btn_all_stop['state'] = 'disabled'

        if self.is_setting_sys_not_sleep:
            self.is_setting_sys_not_sleep = set_system_sleep_state(False, self.text_log)
   
    def select_log_path(self):
        path = filedialog.askdirectory()
        if path:
            self.ety_log_path.delete(0, "end")
            self.ety_log_path.insert(0, path)

    def _init_auto_save_dir(self):
        folder = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        save_dir = get_resource_path(folder)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        self.save_path = save_dir
        self.label_save_path['text'] = self.save_path
        self._text_log_show(f"{self.time_str}: voice recognition Log and images will be saved to {self.save_path}\n")

    def _swtch_btn_asr_start(self):
        if self.use_microphone.get() or self.use_stereo_mix.get():
            self.btn_asr_start['state'] = 'normal'
        else:
            self.btn_asr_start['state'] = 'disabled'

    def _check_stereo_mix(self):
        mic = pyaudio.PyAudio()
        self.stereo_mix_index = find_stereo_mix_device(mic)
        if self.stereo_mix_index is None:
            self._text_log_show(f"{self.time_str}: Stereo Mix not found! Please activate the stereo mix device if you want to listen system output. See help documentation for more details.\n", "red")
        else:
            self._text_log_show(f"{self.time_str}: Can use 'Stereo Mix' device (index={self.stereo_mix_index}) as audio source.\n", "green")

    def _check_has_input_api_model(self):
        # 获取model
        self.model = self.ety_model.get().strip()
        # 检查是否有已有api key
        if self.apikey:
            return True
        # 从配置文件加载
        config = load_config()
        dashscope_key = config.get("dashscope", {}).get("api_key", "")
        if dashscope_key:
            self.apikey = dashscope_key
            self._text_log_show(f"{self.time_str}: Loaded API Key from config.json\n", "green")
            self.ety_api_key.delete(0, "end")
            self.ety_api_key.insert(0, self.apikey)
            return True
        # 没有apikey也没有之前的存储
        api_key = self.ety_api_key.get().strip()
        if not api_key:
            self._text_log_show(f"{self.time_str}: Please input API Key for speech recognition!\n", "red")
            return False
        else:
            self.apikey = api_key
            config["dashscope"]["api_key"] = self.apikey
            save_config(config)
            self._text_log_show(f"{self.time_str}: API Key saved to config.json, and will be auto-loaded on next start.\n", "green")
        return True

    def use_input_api(self):
        self.apikey = self.ety_api_key.get().strip()
        self.model = self.ety_model.get().strip()
        config = load_config()
        config["dashscope"]["api_key"] = self.apikey
        config["dashscope"]["model"] = self.model
        save_config(config)
        self._text_log_show(f"{self.time_str}: Use new input API Key, update to config.json, and will be auto-loaded on next start.\n", "green")

    def _check_api_key_valid(self):
        self._text_log_show(f"{self.time_str}: Checking API Key validity...\n", "blue")
        try:
            dashscope.api_key = self.apikey
            messages = [{'role': 'system', 'content': ' '},
            {'role': 'user', 'content': 'connection test, do not reply anything'}]

            response = dashscope.Generation.call(
                model='qwen-turbo',
                messages=messages,
                result_format='message',  # set the result to be "message" format.
            )

            if response.status_code == HTTPStatus.OK:
                # print(response)
                self._text_log_show(f"{self.time_str}: API Key is valid.\n", "green")
                return True
            else:
                # print('Request id: %s, Status code: %s, error code: %s, error message: %s' % (
                #     response.request_id, response.status_code,
                #     response.code, response.message
                # ))
                self._text_log_show(f"{self.time_str}: API Key is invalid!\n", "red")
                return False
        except Exception as e:
            self._text_log_show(f"{self.time_str}: API Key is invalid!\n", "red")
            return False

    def start_asr(self):
        if not self._check_has_input_api_model():
            return
        if not self._check_api_key_valid():
            return
        self.btn_asr_start['state'] = 'disabled'
        self.btn_asr_stop['state'] = 'normal'
        self.is_speech_recognizing = True

        if not self.is_capturing:
            self._init_auto_save_dir()

        if self.is_capturing:
            self.btn_all_start['state'] = 'disabled'
            self.btn_all_stop['state'] = 'normal'

        self.log_filename = os.path.join(self.save_path, f"asr_log_{time.strftime('%Y%m%d-%H%M%S', time.localtime())}.txt")
        
        if self.use_microphone.get():
            self.asr_proc_mic = multiprocessing.Process(target=run_asr_process, args=(self.log_filename, self.asr_queue, self.apikey, self.model, self.stereo_mix_index, "mic"))
            self.asr_proc_mic.daemon = True
            self.update_mic_state('on')
            self.asr_proc_mic.start()
        if self.use_stereo_mix.get():
            self.asr_proc_stereo = multiprocessing.Process(target=run_asr_process, args=(self.log_filename, self.asr_queue, self.apikey, self.model, self.stereo_mix_index, "stereo mix"))
            self.asr_proc_stereo.daemon = True
            self.update_stereo_mix_state('on')
            self.asr_proc_stereo.start()
        
        self.check_microphone['state'] = 'disabled'
        self.check_stereo_mix['state'] = 'disabled'
        
        self.is_asr_queue_checking = True
        self.poll_asr_queues()

        if not self.is_setting_sys_not_sleep:
            self.is_setting_sys_not_sleep = set_system_sleep_state(True, self.text_log)

    def stop_asr(self):
        self.is_speech_recognizing = False
        self.is_asr_queue_checking = True

        self.btn_asr_start['state'] = 'normal'
        self.btn_asr_stop['state'] = 'disabled'

        self.check_microphone['state'] = 'normal'
        if self.stereo_mix_index:
            self.check_stereo_mix['state'] = 'normal'

        if not self.is_capturing:
            self.btn_all_start['state'] = 'normal'
            self.btn_all_stop['state'] = 'disabled'
        
        # 关闭进程
        if hasattr(self, 'asr_proc_mic') and self.asr_proc_mic.is_alive():
            self.asr_proc_mic.terminate()
            self.asr_proc_mic.join()
            self.update_mic_state('off')
        if hasattr(self, 'asr_proc_stereo') and self.asr_proc_stereo.is_alive():
            self.asr_proc_stereo.terminate()
            self.asr_proc_stereo.join()
            self.update_stereo_mix_state('off')
        

        self.text_asr.insert("end", f"{self.time_str}: Speech recognition stopped.\n")
        self.text_asr.see("end")

        if self.is_setting_sys_not_sleep:
            self.is_setting_sys_not_sleep = set_system_sleep_state(False, self.text_log)
        ...

    def poll_asr_queues(self):
        if not self.is_asr_queue_checking:
            return
        while not self.asr_queue.empty():
            msg = self.asr_queue.get()
            # 检查是否为截图文件名消息
            if msg.startswith("SCREENSHOT:"):
                img_filename = msg.replace("SCREENSHOT:", "")
                screenshot_msg = f"{self.time_str}: [Screenshot captured: {img_filename}]\n"
                self.text_asr.insert("end", screenshot_msg)
                self.text_asr.see("end")
                # 写入语音识别日志文件
                if self.log_filename:
                    with open(self.log_filename, 'a', encoding='utf-8') as f:
                        f.write(screenshot_msg)
            else:
                self.text_asr.insert("end", msg)
                self.text_asr.see("end")
        self.root.after(200, self.poll_asr_queues)  # 200ms轮询一次

    def show_state_window(self):
        if self.is_show_state_window_var.get():
            self.state_window.deiconify()
        else:
            self.state_window.withdraw()

    def __init_state_window(self):
        self.state_window = tk.Toplevel()
        self.state_window.attributes("-topmost", True)  # 窗口置顶
        self.state_window.overrideredirect(True)         # 隐藏窗口的标题栏
        self.state_window.attributes("-alpha", 0.3)      # 窗口透明度10%
        self.state_window.geometry("{0}x{1}+{2}+{3}".format(40, 40, self.win_width - 200, 70))

        self.label_capture_state = tk.Label(self.state_window, text="S-C", bg="orange", font=("Arial", 8))
        self.label_capture_state.place(relx=0.5, rely=0, relwidth=0.5, relheight=0.5)

        self.label_monitoring_state = tk.Label(self.state_window, text="S-M", bg="orange", font=("Arial", 8))
        self.label_monitoring_state.place(relx=0, rely=0, relwidth=0.5, relheight=0.5)
        
        self.label_mic_listening_state = tk.Label(self.state_window, text="Mic", bg="orange", font=("Arial", 8))
        self.label_mic_listening_state.place(relx=0, rely=0.5, relwidth=0.5, relheight=0.5)

        self.label_stereo_mix_listening_state = tk.Label(self.state_window, text="Mix", bg="orange", font=("Arial", 8))
        self.label_stereo_mix_listening_state.place(relx=0.5, rely=0.5, relwidth=0.5, relheight=0.5)

        self.state_window.bind("<Button-1>", self._state_window_on_start)
        self.state_window.bind("<B1-Motion>", self._state_window_on_drag)
        def toggle_root(event):
            if self.root.state() == "normal":
                self.root.iconify()
            else:
                self.root.deiconify()
                self.root.lift()
        self.state_window.bind("<Double-Button-1>", toggle_root)

        # 右键菜单
        self.state_menu = tk.Menu(self.state_window, tearoff=0)
        self.state_menu.add_command(label="Start Capture", command=self.start_capture)
        self.state_menu.add_command(label="Stop Capture", command=self.stop_capture)
        self.state_menu.add_command(label="Start ASR", command=self.start_asr)
        self.state_menu.add_command(label="Stop ASR", command=self.stop_asr)
        self.state_menu.add_command(label="Start All", command=self.start_all)
        self.state_menu.add_command(label="Stop All", command=self.stop_all)

        def show_state_menu(event):
            # 根据按钮状态设置菜单项可用/禁用
            self.state_menu.entryconfig("Start Capture", state="normal" if self.btn_start['state']=="normal" else "disabled")
            self.state_menu.entryconfig("Stop Capture", state="normal" if self.btn_stop['state']=="normal" else "disabled")
            self.state_menu.entryconfig("Start ASR", state="normal" if self.btn_asr_start['state']=="normal" else "disabled")
            self.state_menu.entryconfig("Stop ASR", state="normal" if self.btn_asr_stop['state']=="normal" else "disabled")
            self.state_menu.entryconfig("Start All", state="normal" if self.btn_all_start['state']=="normal" else "disabled")
            self.state_menu.entryconfig("Stop All", state="normal" if self.btn_all_stop['state']=="normal" else "disabled")
            self.state_menu.tk_popup(event.x_root, event.y_root)

        self.state_window.bind("<Button-3>", show_state_menu)
    
    def _state_window_on_start(self, event):
        self.mouse_x, self.mouse_y = event.x, event.y

    def _state_window_on_drag(self, event):
        x, y = event.x, event.y
        self.state_window.geometry(f"{40}x{40}+{self.state_window.winfo_x() + x - self.mouse_x}+{self.state_window.winfo_y() + y - self.mouse_y}")

    def _state_window_on_stop(self, event):
        self.mouse_x, self.mouse_y = 0, 0

    def update_monitoring_state(self, func='off'):
        if func == 'on':
            self.label_monitoring_state["bg"] = "red"
        elif func =='off':
            self.label_monitoring_state["bg"] = "orange"
            
    def update_capture_state(self, func='off'):
        if func == 'on':
            self.label_capture_state["bg"] = "red"
            self.state_window.after(min(500, int(self.capture_interval * 1000 / 2)), lambda: self.update_capture_state('off'))
        elif func == 'off':
            self.label_capture_state["bg"] = "orange"

    def update_mic_state(self, func='off'):
        if func == 'on':
            self.label_mic_listening_state["bg"] = "red"
        elif func == 'off':
            self.label_mic_listening_state["bg"] = "orange"

    def update_stereo_mix_state(self, func='off'):
        if func == 'on':
            self.label_stereo_mix_listening_state["bg"] = "red"
        elif func == 'off':
            self.label_stereo_mix_listening_state["bg"] = "orange"

    def get_capture_window(self):
        self.root.iconify() # 最小化窗口
        cws = Capture_window_select(self.capture_window)
        self.root.deiconify() # 还原窗口
        self.capture_window = cws.get_capture_window_coor()
        # 显示截图区域信息到文本框, 包含时间
        self.text_info.insert("end", f"{self.time_str}:\n   Capture window:{self.capture_window}\n")
        self.text_info.see("end")
        self.label_capture_window['text'] = f"({self.capture_window[0]},{self.capture_window[1]})->({self.capture_window[2]},{self.capture_window[3]})"
        if self.capture_window is not None:
            self.btn_start['state'] = 'normal'

    def _update_monitoring_countdown(self):
        if not self.is_capturing:
            self.label_monitoring_state["text"] = "S-M"
            return
        remaining_time = self.capture_interval - self.monitoring_countdown
        self.label_monitoring_state["text"] = f"{remaining_time:.0f}"
        self.monitoring_countdown += 1
        if remaining_time > 0:
            self.state_window.after(1000, self._update_monitoring_countdown)

    def capture(self):
        self.update_capture_state('off')        
        self.monitoring_countdown = 0
        self._update_monitoring_countdown()

        im2 = ImageGrab.grab(bbox=self.capture_window, include_layered_windows=False, all_screens=True)

        diff = ImageChops.difference(self.im, im2)
        diff = sum(ImageStat.Stat(diff).mean)
        # diff = np.mean((np.array(self.im) - np.array(im2))**2) / (self.im_l * self.im_w)
        if  diff > self.sensitivity:
            if self.is_capturing:
                img_path = os.path.join(self.save_path, f'{self.time_str}.png')
                im2.save(img_path)
                self.text_info.insert("end", f"\n{self.time_str}:\n   diff={diff:.1f}, PPT slide change detected!\n")
                self.text_info.see("end")
                self.update_capture_state('on')
                # 如果语音识别已启动，将图片文件名添加到ASR队列
                if self.is_speech_recognizing:
                    img_filename = os.path.basename(img_path)
                    self.asr_queue.put(f"SCREENSHOT:{img_filename}")
        else:
            if self.is_capturing: 
                self.text_info.insert("end", f"E={diff:.1f};")
                self.text_info.see("end")
        
        self.im = im2

        if not self.is_capturing:
            return
        
        self.root.after(int(self.capture_interval * 1000), self.capture)

    def start_capture(self):
        self.is_capturing = True
        self.capture_interval = float(self.ety_capture_interval.get())
        self.sensitivity = self.scb_sensitivity.get()
        self.text_info.insert("end", f"\n{self.time_str}:\n   Capture started!\n")
        self.text_info.insert("end", f"   Check interval={self.capture_interval}s, sensitivity={self.sensitivity}\n")
        self.text_info.see("end")
        self.btn_start['state'] = 'disabled'
        self.btn_stop['state'] = 'normal'
        self.btn_window_config['state'] = 'disabled'

        if not self.is_speech_recognizing:
            self._init_auto_save_dir()

        self.im = ImageGrab.grab(bbox=self.capture_window, include_layered_windows=False, all_screens=True)
        self.im.save(rf'{self.save_path}\{self.time_str}.png')
        if self.is_speech_recognizing:
            img_filename = os.path.basename(rf'{self.save_path}\{self.time_str}.png')
            self.asr_queue.put(f"SCREENSHOT:{img_filename}")

        self.im_l, self.im_w = self.im.size
        self.im_l, self.im_w = self.im_l/1000, self.im_w/1000

        if self.is_speech_recognizing:
            self.btn_all_start['state'] = 'disabled'
            self.btn_all_stop['state'] = 'normal'

        if not self.is_setting_sys_not_sleep:
            self.is_setting_sys_not_sleep = set_system_sleep_state(True, self.text_log)

        self.update_monitoring_state('on')
        self.capture()

    def stop_capture(self):
        self.text_info.insert("end", f"\n{self.time_str}:\n   Capture stopped!\n")
        self.text_info.see("end")
        self.btn_start['state'] = 'normal'
        self.btn_stop['state'] = 'disabled'
        self.is_capturing = False

        if not self.is_speech_recognizing:
            self.btn_all_start['state'] = 'normal'
            self.btn_all_stop['state'] = 'disabled'

        self.label_monitoring_state["bg"] = "orange"
        self.label_capture_state["bg"] = "orange"

        if self.is_setting_sys_not_sleep:
            self.is_setting_sys_not_sleep = set_system_sleep_state(False, self.text_log)

        self.update_monitoring_state('off')

    def sys_out(self):
        self.stop_all()
        set_system_sleep_state(False, self.text_log)
        self.root.destroy()
        self.root.quit()

    def on_close(self):
        self.stop_all()
        set_system_sleep_state(False, self.text_log)
        self.root.destroy()
        self.root.quit()

    def open_save_path(self):
        if self.save_path and os.path.exists(self.save_path):
            os.startfile(self.save_path)
        else:
            self.text_log.insert("end", f"{self.time_str}: No valid save path!\n")
            self.text_log.see("end")

    def show_help(self):
        # Window 1: show help_image.png
        help_img_path = get_resource_ico_path("asset/help_image.png")
        win_img = tk.Toplevel(self.root)
        win_img.title("Help Image")
        try:
            img = Image.open(help_img_path)
            # Initial scale 50%
            scale = 0.3
            img_resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.BICUBIC)
            tk_img = ImageTk.PhotoImage(img_resized)
            label_img = tk.Label(win_img, image=tk_img)
            label_img.image = tk_img
            label_img.pack()
        except Exception as e:
            tk.Label(win_img, text=f"Image not found: {help_img_path}\n{e}", fg="red").pack()

        # Window 2: show Markdown help text
        win_md = tk.Toplevel(self.root)
        win_md.title("Help Text")
        help_md_path = get_resource_ico_path("asset/help_md.md")
        try:
            with open(help_md_path, "r", encoding="utf-8") as f:
                md_text = f.read()
        except Exception as e:
            md_text = "# Help\nNo help_text.md found.\n" + str(e)
        text_widget = tk.Text(win_md, wrap="word")
        text_widget.insert("end", md_text)
        text_widget.pack(fill="both", expand=True)
        text_widget.config(state="disabled")

        # 显示一个按钮，点击后连接至项目GitHub页面
        btn_github = tk.Button(win_md, text="See in GitHub", command=self.open_github)
        btn_github.pack(pady=10)

    def open_github(self):
        webbrowser.open("https://github.com/ChenChenGith/Video_PPT_capture")

    @property
    def time_str(self):
        return time.strftime("%Y%m%d-%H%M%S", time.localtime())

    def open_minutes_summary(self):
        """打开会议纪要整理窗口"""
        MinutesSummaryWindow(self.root, self.save_path if self.save_path else os.path.abspath("."))

# 会议纪要整理窗口类
class MinutesSummaryWindow:
    def __init__(self, parent, default_dir):
        self.window = tk.Toplevel(parent)
        self.window.title("Minutes Summary")
        self.window.geometry("500x350")

        # 主frame
        self.main_frame = tk.Frame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # LLM API设置
        self.frame_llm = tk.LabelFrame(self.main_frame, text="LLM API Settings", font=("Arial", 10, "bold"))
        self.frame_llm.pack(fill="x", pady=5)

        tk.Label(self.frame_llm, text="API URL").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.ety_api_url = tk.Entry(self.frame_llm, width=40)
        self.ety_api_url.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(self.frame_llm, text="API Key").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.ety_api_key = tk.Entry(self.frame_llm, show="*", width=40)
        self.ety_api_key.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        tk.Label(self.frame_llm, text="Model").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.ety_model = tk.Entry(self.frame_llm, width=40)
        self.ety_model.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        self.btn_update_llm_config = tk.Button(self.frame_llm, text="Update LLM Config to config.json", command=self.save_llm_config)
        self.btn_update_llm_config.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.frame_llm.columnconfigure(1, weight=1)

        # 目录选择
        self.frame_dir = tk.LabelFrame(self.main_frame, text="Meeting Directory", font=("Arial", 10, "bold"))
        self.frame_dir.pack(fill="x", pady=5)

        tk.Label(self.frame_dir, text="Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.label_dir = tk.Label(self.frame_dir, text=default_dir, fg="blue", anchor="w", wraplength=350)
        self.label_dir.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.btn_browse = tk.Button(self.frame_dir, text="Browse", command=self.browse_directory)
        self.btn_browse.grid(row=0, column=2, padx=5, pady=2)

        # 运行按钮
        self.btn_run = tk.Button(self.main_frame, text="Run Minutes Summary", command=self.run_summary, bg="green", fg="white", font=("Arial", 11, "bold"))
        self.btn_run.pack(fill="x", pady=(20, 5))

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.label_status = tk.Label(self.main_frame, textvariable=self.status_var, fg="gray", anchor="w", relief="sunken", bd=1)
        self.label_status.pack(fill="x", pady=(10, 0))

        # 加载已保存的配置
        self.load_llm_config()
        self.working_dir = default_dir

        # 初始化运行状态
        self.is_running = False

    def load_llm_config(self):
        """加载LLM API配置"""
        config = load_config()
        llm_config = config.get("llm", {})
        self.ety_api_url.insert(0, llm_config.get("api_url", ""))
        self.ety_api_key.insert(0, llm_config.get("api_key", ""))
        self.ety_model.insert(0, llm_config.get("model", ""))

    def save_llm_config(self):
        """保存LLM API配置"""
        config = load_config()
        config["llm"]["api_url"] = self.ety_api_url.get().strip()
        config["llm"]["api_key"] = self.ety_api_key.get().strip()
        config["llm"]["model"] = self.ety_model.get().strip()
        save_config(config)
        self.update_status("LLM config saved successfully!", "green")

    def browse_directory(self):
        """浏览并选择会议目录"""
        directory = filedialog.askdirectory(initialdir=self.working_dir, parent=self.window)
        if directory:
            self.working_dir = directory
            self.label_dir.config(text=directory)

    def update_status(self, message, color="gray"):
        """更新状态栏"""
        self.status_var.set(message)
        self.label_status.config(fg=color)

    def run_summary(self):
        """运行会议纪要整理"""
        # 保存LLM配置
        self.save_llm_config()

        api_url = self.ety_api_url.get().strip()
        api_key = self.ety_api_key.get().strip()
        model = self.ety_model.get().strip()

        if not api_url or not api_key or not model:
            self.update_status("Error: Please fill in all LLM API settings!", "red")
            return

        # 检查目录是否存在
        if not os.path.exists(self.working_dir):
            self.update_status(f"Error: Directory {self.working_dir} does not exist!", "red")
            return

        # 查找asr_log文件
        asr_files = [f for f in os.listdir(self.working_dir) if f.startswith("asr_log_") and f.endswith(".txt")]
        if not asr_files:
            self.update_status("Error: No ASR log files found in the directory!", "red")
            return

        # 读取最新的日志文件
        asr_files.sort(reverse=True)
        asr_file_path = os.path.join(self.working_dir, asr_files[0])

        try:
            with open(asr_file_path, 'r', encoding='utf-8') as f:
                asr_content = f.read()
        except Exception as e:
            self.update_status(f"Error reading ASR log: {str(e)}", "red")
            return

        # 检查目录中是否有图片
        image_files = [f for f in os.listdir(self.working_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        image_files.sort()  # 按文件名排序

        # 从配置文件读取prompt模板
        config = load_config()
        prompt_config = config.get("prompt", {})

        # 构建prompt
        if not image_files:
            # 没有图片：纯会议纪要
            prompt_template = prompt_config.get("no_image")
            if prompt_template:
                prompt = prompt_template.format(asr_content=asr_content)
            else:
                # 使用默认模板
                prompt = f"""请将以下会议录音内容整理成Markdown格式的会议纪要。

要求：
1. 提取会议主题、时间、参与者等基本信息
2. 总结会议的主要讨论内容
3. 列出关键决策和行动项
4. 使用清晰的Markdown格式，包括标题、列表等

会议录音内容：
{asr_content}
"""
        else:
            # 有图片：按截图顺序整理
            prompt_template = prompt_config.get("with_image")
            if prompt_template:
                image_list = "\n".join([f"- {img}" for img in image_files])
                prompt = prompt_template.format(
                    image_count=len(image_files),
                    asr_content=asr_content,
                    image_list=image_list
                )
            else:
                # 使用默认模板
                prompt_parts = []
                prompt_parts.append(f"请将以下会议录音内容整理成Markdown格式的会议纪要。")
                prompt_parts.append(f"会议中共有{len(image_files)}张PPT截图，请按照截图出现的时间顺序，为每张截图编写对应的主旨摘要。")
                prompt_parts.append(f"截图标记格式为：'[SCREENSHOT: 文件名]'，请根据截图标记将录音内容分段。")
                prompt_parts.append(f"输出格式要求：每张截图显示后，紧接对应的主旨摘要，截图要采用Markdown图片语法来引入。")

                prompt_parts.append(f"\n会议录音内容：")
                prompt_parts.append(asr_content)

                prompt_parts.append(f"\n\n可用的截图文件列表：")
                for img in image_files:
                    prompt_parts.append(f"- {img}")

                prompt_parts.append(f"\n\n请输出Markdown格式的会议纪要。")
                prompt = "\n".join(prompt_parts)

        # 禁用按钮，启动后台线程
        self.btn_run.config(state="disabled")
        self.update_status("Starting LLM API call...", "blue")

        # 记录开始时间，启动计时器
        self.start_time = time.time()
        self.is_running = True
        self._update_timer()

        # 启动后台线程执行LLM调用
        import threading
        thread = threading.Thread(target=self._run_summary_thread, args=(api_url, api_key, model, prompt))
        thread.daemon = True
        thread.start()

    def _update_timer(self):
        """更新计时器显示"""
        if self.is_running:
            elapsed = int(time.time() - self.start_time)
            self.update_status(f"Running... Elapsed: {elapsed}s", "blue")
            # 每秒更新一次
            self.window.after(1000, self._update_timer)

    def _run_summary_thread(self, api_url, api_key, model, prompt):
        """后台线程执行LLM调用"""
        try:
            # 构建API请求（OpenAI协议格式）
            # 确保URL包含完整的endpoint路径
            if "/chat/completions" not in api_url:
                if api_url.endswith("/"):
                    api_url = api_url + "chat/completions"
                else:
                    api_url = api_url + "/chat/completions"

            # 更新状态：正在调用API
            self.window.after(0, lambda: self.update_status("Calling LLM API, please wait...", "blue"))

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的会议纪要助手，擅长整理会议内容并生成结构化的Markdown文档。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }

            # 更新状态：发送请求
            self.window.after(0, lambda: self.update_status("Sending request to LLM API...", "blue"))

            response = requests.post(api_url, headers=headers, json=payload, timeout=300)

            if response.status_code == 200:
                # 更新状态：处理响应
                self.window.after(0, lambda: self.update_status("Processing LLM response...", "blue"))

                result = response.json()
                # 根据不同API格式提取内容
                if "choices" in result:
                    markdown_content = result["choices"][0]["message"]["content"]
                else:
                    markdown_content = str(result)

                # 保存为.md文件
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                md_filename = f"minutes_summary_{timestamp}.md"
                md_filepath = os.path.join(self.working_dir, md_filename)

                with open(md_filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                # 更新状态：成功
                self.window.after(0, lambda: self.update_status(f"Success! Saved to: {md_filepath}", "green"))
            else:
                # 更新状态：失败
                error_msg = f"LLM API call failed: {response.status_code}"
                self.window.after(0, lambda: self.update_status(error_msg, "red"))

        except requests.exceptions.Timeout:
            self.window.after(0, lambda: self.update_status("Error: LLM API call timeout!", "red"))
        except Exception as e:
            self.window.after(0, lambda: self.update_status(f"Error: {str(e)}", "red"))
        finally:
            # 停止计时器，恢复按钮状态
            self.is_running = False
            self.window.after(0, lambda: self.btn_run.config(state="normal"))

if __name__ == "__main__":
    multiprocessing.freeze_support()  # 兼容 Windows exe
    ScreenCapture()