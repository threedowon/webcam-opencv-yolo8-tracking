"""
빌드 전 버전 업그레이드: version.txt 마지막 자리 +1 (예: 1.0.0 -> 1.0.1)
실행: python bump_version.py
"""
import os

version_file = os.path.join(os.path.dirname(__file__), "version.txt")
with open(version_file, "r", encoding="utf-8") as f:
    line = f.read().strip()
current = line.split("#")[0].strip() or "1.0.0"
parts = current.split(".")
parts[-1] = str(int(parts[-1]) + 1)
new_version = ".".join(parts)

with open(version_file, "w", encoding="utf-8") as f:
    f.write(new_version + "\n")

print(f"Version: {current} -> {new_version}")
