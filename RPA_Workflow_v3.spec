# -*- mode: python ; coding: utf-8 -*-
# ============================================================
# RPA_Workflow_v3 PyInstaller 编译配置（由 v3/build.bat 调用）
#
# 调用方式:  pyinstaller RPA_Workflow_v3.spec --distpath <输出目录>
# 参数化说明: --distpath 由 build.bat 通过命令行传入覆盖，
#             保证输出路径参数化能力不丢失（本 spec 内不硬编码输出路径）。
# ============================================================

# ---- 入口与依赖分析 ----
a = Analysis(
    # 入口文件: rpa_engine/main.py（GUI 唯一交互入口）。
    # 不选 gui/app.py 的原因: app.py 无 __main__ 守卫，无法独立作为打包入口；
    # main.py 调用 gui.app.launch_gui() 启动四阶段应用。
    ['rpa_engine/main.py'],
    # 模块搜索路径: main.py 使用顶层绝对导入（from engine.parser import ...），
    # 需将 rpa_engine 目录加入搜索路径，使 engine/gui 可作为顶层包解析。
    pathex=['rpa_engine'],
    binaries=[],
    # 携带数据目录:
    #   templates — 预设模板目录（只读资源，frozen 下经 paths.get_bundle_dir()
    #               定位于 _MEIPASS/templates）；用户模板目录 templates/user 为
    #               运行时创建于 exe 所在目录（paths.get_engine_root()），不打包
    #   config    — 仓库中不存在该目录（引擎无独立配置文件，配置取自工作流 JSON
    #               的 global 字段），故不携带
    datas=[('rpa_engine/templates', 'templates')],
    hiddenimports=[
        # v3.1：操作函数层为动态引用面（engine.registry / gui.app 均经
        # importlib 或跨包引用 ops），显式声明 ops 包及其全部模块，
        # 保证 BUILTIN_OPS 用户操作目录完整打包。
        # paths：运行环境自适应路径解析（部分模块函数内延迟 import，
        # 静态分析可能遗漏，显式声明保证打包）。
        'paths',
        'ops',
        'ops.sql_safety',
        'ops.session_db',
        'ops.excel_preprocessor',
        'ops.sqlite_manager',
        'ops.table_importer',
        'ops.table_lifecycle',
        'ops.table_schema',
        'ops.table_content',
        'ops.filter_dedup',
        'ops.mapping_matcher',
        'ops.aggregator',
        'ops.exporter',
        'ops.supervision_report',
        'ops.step_executor',
        # R11/A-17：xlrd 以字符串形式传给 pandas.read_excel(engine="xlrd")，
        # 全库从未 import 该模块 → PyInstaller 静态分析收集不到，须显式声明。
        'xlrd',
        # R11/A-17：P3 将新建的规范化模块（预先登记，防 exe 重建时遗漏）。
        'ops.excel_normalizer',
        # 任务要求显式声明的隐式依赖（openpyxl 虽已被 exporter 静态导入，
        # 此处再声明一层作为保险）。
        'openpyxl',
        # PyQt5 打包的常见隐式依赖（sip 绑定模块）。
        'PyQt5.sip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# ---- 字节码打包 ----
pyz = PYZ(a.pure, a.zipped_data)

# ---- 单文件可执行程序（--onefile + --windowed） ----
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,                # 单文件模式: 全部二进制依赖打入 exe
    a.zipfiles,
    a.datas,                   # 单文件模式: 数据文件（templates）打入 exe
    [],
    name='RPA_Workflow_v3',    # 输出文件名（任务规定）
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # 不启用 UPX 压缩（降低杀软误报概率）
    runtime_tmpdir=None,       # 运行时解压到系统默认临时目录
    console=False,             # --windowed: GUI 程序，无控制台窗口
    # 图标: 项目暂无图标文件（gui/assets/app.ico 不存在），故置 None；
    # 后续如补充图标文件，将此行改为 icon=r'rpa_engine\gui\assets\app.ico'
    icon=None,
)
