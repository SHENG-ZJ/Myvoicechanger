import customtkinter as ctk
import sounddevice as sd
import numpy as np
from pedalboard import Pedalboard, PitchShift, Compressor, NoiseGate, HighpassFilter, PeakFilter
import threading


# --- 核心引擎 (防卡顿配置) ---
class AudioEngine:
    def __init__(self):
        self.stream = None
        self.running = False
        self.sample_rate = None
        self.block_size = 4096  # 4096 = 稳定防卡顿

        # 效果链
        self.noise_gate = NoiseGate(threshold_db=-40, ratio=4, attack_ms=1.0, release_ms=100)
        self.hp_filter = HighpassFilter(cutoff_frequency_hz=80)
        self.pitch_shift = PitchShift(semitones=0)
        self.formant_filter = PeakFilter(cutoff_frequency_hz=2000, gain_db=0, q=1.0)
        self.compressor = Compressor(threshold_db=-20, ratio=3, attack_ms=2, release_ms=200)

        self.board = Pedalboard([
            self.noise_gate, self.hp_filter, self.pitch_shift, self.formant_filter, self.compressor
        ])

    def set_pitch(self, semitones):
        self.pitch_shift.semitones = semitones
        # 自动共振峰微调
        if semitones > 0:
            self.formant_filter.cutoff_frequency_hz = 2500
            self.formant_filter.gain_db = semitones * 0.5
        else:
            self.formant_filter.cutoff_frequency_hz = 300
            self.formant_filter.gain_db = abs(semitones) * 0.8

    def start(self, input_idx, output_idx):
        if self.running: return
        try:
            dev_info = sd.query_devices(input_idx, 'input')
            self.sample_rate = int(dev_info['default_samplerate'])
            self.stream = sd.Stream(
                device=(input_idx, output_idx),
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype='float32',
                channels=1,
                callback=self.callback
            )
            self.stream.start()
            self.running = True
            return True, "OK"
        except Exception as e:
            return False, str(e)

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.running = False

    def callback(self, indata, outdata, frames, time, status):
        try:
            processed = self.board(indata.T, sample_rate=self.sample_rate).T
            outdata[:] = processed
        except:
            outdata[:] = indata


# --- 极简 GUI ---
class MiniVoiceChanger(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("小琛哥变声器")
        self.geometry("280x210")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")

        self.engine = AudioEngine()
        self.input_list, self.output_list = [], []
        self.dev_map_in, self.dev_map_out = [], []

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._init_ui()
        self._refresh_devices()

    def _init_ui(self):
        # 1. 设备选择
        self.input_combo = ctk.CTkComboBox(self.main_frame, width=250, height=24)
        self.input_combo.set("正在加载设备...")
        self.input_combo.pack(pady=(5, 5))

        self.output_combo = ctk.CTkComboBox(self.main_frame, width=250, height=24)
        self.output_combo.set("正在加载设备...")
        self.output_combo.pack(pady=(0, 15))

        # 2. 音调控制
        self.pitch_label = ctk.CTkLabel(self.main_frame, text="音色: 0.0", font=("Arial", 16, "bold"))
        self.pitch_label.pack(pady=0)

        self.pitch_slider = ctk.CTkSlider(
            self.main_frame, from_=-3, to=3, number_of_steps=30, width=240,
            command=self._on_pitch_change
        )
        self.pitch_slider.set(0)
        self.pitch_slider.pack(pady=(5, 20))

        # 3. 开关
        self.btn_toggle = ctk.CTkButton(
            self.main_frame, text="START", height=50, width=200,
            font=("Arial", 16, "bold"), fg_color="#2CC985", hover_color="#229966",
            command=self._toggle_engine
        )
        self.btn_toggle.pack(side="bottom", pady=10)

    def _refresh_devices(self):
        """完全重写的智能设备刷新逻辑"""
        try:
            devices = sd.query_devices()
            hostapis = sd.query_hostapis()

            # 1. 寻找最常用的 API (Windows上选MME以获得最干净的列表，Mac选Core Audio)
            # 这样可以避免同一个设备出现3次 (MME, WASAPI, DirectSound...)
            valid_api_index = sd.default.hostapi

            self.input_list, self.output_list = [], []
            self.dev_map_in, self.dev_map_out = [], []

            for i, d in enumerate(devices):
                # 只显示默认 API 的设备，或者 API 数量很少时全显示
                if len(hostapis) > 1 and d['hostapi'] != valid_api_index:
                    continue

                name = d['name']
                lower_name = name.lower()

                # --- 智能过滤输入设备 ---
                # 排除含有 "Speaker", "扬声器", "Mapper" 的设备
                if d['max_input_channels'] > 0:
                    if "speaker" not in lower_name and "扬声器" not in lower_name and "mapper" not in lower_name:
                        self.input_list.append(name)
                        self.dev_map_in.append(i)

                # --- 智能过滤输出设备 ---
                # 排除含有 "Microphone", "麦克风" 的设备
                if d['max_output_channels'] > 0:
                    if "microphone" not in lower_name and "麦克风" not in lower_name and "mapper" not in lower_name:
                        self.output_list.append(name)
                        self.dev_map_out.append(i)

            self.input_combo.configure(values=self.input_list)
            self.output_combo.configure(values=self.output_list)

            # 智能预选
            if self.input_list:
                self.input_combo.set(self.input_list[0])
            else:
                self.input_combo.set("未找到麦克风")

            if self.output_list:
                # 优先选 Cable / BlackHole
                cable = next((x for x in self.output_list if "Cable" in x or "BlackHole" in x), self.output_list[0])
                self.output_combo.set(cable)
            else:
                self.output_combo.set("未找到扬声器")

        except Exception as e:
            print(f"Error refreshing devices: {e}")

    def _on_pitch_change(self, val):
        formatted_val = round(float(val), 1)
        self.pitch_label.configure(text=f"音色: {formatted_val}")
        self.engine.set_pitch(formatted_val)

    def _toggle_engine(self):
        if not self.engine.running:
            cur_in, cur_out = self.input_combo.get(), self.output_combo.get()

            # 安全检查
            if cur_in not in self.input_list:
                print("无效的输入设备")
                return
            if cur_out not in self.output_list:
                print("无效的输出设备")
                return

            in_idx = self.dev_map_in[self.input_list.index(cur_in)]
            out_idx = self.dev_map_out[self.output_list.index(cur_out)]

            if in_idx == out_idx: return

            success, _ = self.engine.start(in_idx, out_idx)
            if success:
                self.btn_toggle.configure(text="STOP", fg_color="#FF4444", hover_color="#CC3333")
                self.input_combo.configure(state="disabled")
                self.output_combo.configure(state="disabled")
        else:
            self.engine.stop()
            self.btn_toggle.configure(text="START", fg_color="#2CC985", hover_color="#229966")
            self.input_combo.configure(state="normal")
            self.output_combo.configure(state="normal")

    def on_closing(self):
        self.engine.stop()
        self.destroy()


if __name__ == "__main__":
    app = MiniVoiceChanger()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()