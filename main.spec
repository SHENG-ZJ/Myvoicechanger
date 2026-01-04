# main.spec
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all
import customtkinter

block_cipher = None

# 自动获取 customtkinter 的路径，防止资源丢失
ctk_path = os.path.dirname(customtkinter.__file__)

# 收集 pedalboard 的所有资源 (防止音频插件加载失败)
datas, binaries, hiddenimports = collect_all('pedalboard')

# 添加 customtkinter 数据
datas.append((ctk_path, 'customtkinter'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VoiceChanger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Mac GUI 程序不需要控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 生成 macOS 的 .app 包
app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='VoiceChanger.app',
    icon=None, # 如果你有图标，填入 'icon.icns'
    bundle_identifier='com.yourname.voicechanger',
)