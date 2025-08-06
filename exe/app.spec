import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = (
    ['yandex_flow', 'app_utils', 'app_ui']
    + collect_submodules('app_ui')
    + collect_submodules('app_utils')
    + collect_submodules('patchright')
    + collect_submodules('patchright.async_api')
    + collect_submodules('patchright._impl')


)

root = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..'))

a = Analysis(
    [os.path.join(root, 'app.py')],
    pathex=[root],
    binaries=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    excludes=['test_app'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    datas=[
        ('C:/Users/vovoc/Desktop/1/yandexservices/.venv/Lib/site-packages/patchright/driver', 'patchright/driver'),
    ],
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    bootloader_ignore_signals=False,
    onefile=True,
    icon=None,
)

# куда складывать
exe.distpath = os.path.join(root, 'exe')
exe.workpath = os.path.join(root, 'build')
