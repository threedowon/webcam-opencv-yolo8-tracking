@echo off
cd /d D:\IMFINE\LSA_LuckyFlip_Wall\Python
python bump_version.py
python -m PyInstaller --onefile --name OrbbecTracker --icon "D:\IMFINE\LSA_LuckyFlip_Wall\Python\lotte.ico" --add-data "D:\IMFINE\LSA_LuckyFlip_Wall\Python\version.txt;." orbbec.py
pause