# -*- mode: python -*-

block_cipher = None


a = Analysis(['a3.py'],
             pathex=['/Users/h4sh/Documents/CSSE1001/3'],
             binaries=[],
             datas=[('images', 'images/')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='a3',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
