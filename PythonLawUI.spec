block_cipher = None

a = Analysis(
    ['PythonLawUI.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'Fileorganizer_python',  # Your backend module
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'configparser',
        'pathlib',
        'threading',
        'datetime',
        'collections',
        'time',
        'PyPDF2',  # PDF processing
        'docx',  # python-docx for DOCX files
        'ahocorasick',  # Fast string matching (optional)
        'openpyxl',  # For Excel file reading (pandas dependency)
        'xlrd',  # For older Excel formats
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # Exclude unused heavy libraries
        'numpy.random._examples',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LawyerFileOrganizer',  # More professional name
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon='icon.ico' if you have one
)

# Optional: Create a single-file executable (commented out for faster builds)
# To enable single-file mode, uncomment below and comment out the EXE block above:
"""
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LawyerFileOrganizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    onefile=True,  # Single executable file
)
"""