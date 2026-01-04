import PyInstaller.__main__
import customtkinter
import os
import platform

# 1. 获取 customtkinter 库的安装路径 (自动寻找，无需手动查)
ctk_path = os.path.dirname(customtkinter.__file__)

# 2. 确定分隔符 (Windows用分号, Mac/Linux用冒号)
sep = ';' if platform.system() == "Windows" else ':'

# 3. 运行 PyInstaller
PyInstaller.__main__.run([
    'main.py',                       # 你的主程序文件名 (如果是其他名字请修改这里)
    '--name=小琛哥变声器',           # 生成的软件名字
    '--noconsole',                   # 不显示黑色命令行窗口
    '--onefile',                     # 打包成单个文件 (由文件夹变成一个独立程序)
    '--clean',                       # 清理缓存
    f'--add-data={ctk_path}{sep}customtkinter', # 关键：把 ctk 的资源文件塞进去
])