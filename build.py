import PyInstaller.__main__
import customtkinter
import os
import platform

# 获取 ctk 路径
ctk_path = os.path.dirname(customtkinter.__file__)
sep = ';' if platform.system() == "Windows" else ':'

PyInstaller.__main__.run([
    'main.py',
    '--name=VoiceChanger',
    '--noconsole',
    '--onedir',   # <--- 关键修改：改为 onedir (文件夹模式)
    '--clean',
    f'--add-data={ctk_path}{sep}customtkinter',
    # 强制让 macOS 把依赖打进去
    '--collect-all=pedalboard', 
    '--collect-all=sounddevice'
])
