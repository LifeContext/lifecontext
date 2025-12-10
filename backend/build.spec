# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(SPEC))

block_cipher = None

# 收集数据文件
datas = []
datas += collect_data_files('flask')
datas += collect_data_files('chromadb')
datas += collect_data_files('sentence_transformers')

# 添加项目特定文件
project_files = [
    ('config.py', '.'),
    ('utils', 'utils'),
    ('routes', 'routes'),
    ('tools', 'tools'),
    ('scheduler.py', '.'),
    ('.env.example', '.'),
]

for src, dst in project_files:
    src_path = os.path.join(current_dir, src)
    if os.path.exists(src_path):
        if os.path.isdir(src_path):
            # 递归添加目录中的所有文件
            for root, dirs, files in os.walk(src_path):
                # 排除 __pycache__ 目录
                dirs[:] = [d for d in dirs if d != '__pycache__']
                for file in files:
                    if file.endswith('.py') or file.endswith('.yml') or file.endswith('.yaml'):
                        file_path = os.path.join(root, file)
                        rel_dir = os.path.relpath(root, src_path)
                        if rel_dir == '.':
                            target_dir = dst
                        else:
                            target_dir = os.path.join(dst, rel_dir)
                        datas.append((file_path, target_dir))
        else:
            datas.append((src_path, dst))

# 隐藏导入
hiddenimports = [
    'flask',
    'flask_cors',
    'chromadb',
    'chromadb.config',
    'chromadb.api',
    'chromadb.db',
    'sentence_transformers',
    'sentence_transformers.models',
    'torch',
    'transformers',
    'APScheduler',
    'openai',
    'tiktoken',
    'dotenv',
    'json_repair',
    'asyncio',
    'threading',
    'concurrent.futures',
]

# 收集所有子模块
hiddenimports += collect_submodules('sentence_transformers')
hiddenimports += collect_submodules('chromadb')

a = Analysis(
    ['app.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'notebook',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LifeContextBackend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)