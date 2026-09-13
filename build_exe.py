import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'viewer.py',
    '--onefile',
    '--windowed',
    '--name=pdf-viewer',
    '--add-data=meinkampf.pdf;.',
    '--hidden-import=fitz',
    '--hidden-import=fitz.utils',
    '--hidden-import=fitz.fitz',
    '--clean',
    '--noconfirm',
])