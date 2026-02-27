# OrbbecTracker 빌드

## 버전 업그레이드 (빌드할 때마다)

버전은 **version.txt**에만 둡니다 (.py에 넣지 않음).

- **빌드 전에** 아래 중 하나 실행해서 버전을 올리세요.
- `version.txt` 형식: `1.0.0` → 한 번 올리면 `1.0.1`, 다시 올리면 `1.0.2` …

### 방법 1: 스크립트 실행 (권장)

```bash
python bump_version.py
```

- `version.txt`의 마지막 자리를 1 올립니다 (1.0.0 → 1.0.1).

### 방법 2: 수동

- `version.txt`를 열어서 마지막 숫자만 1 증가시킨 뒤 저장.

---

## PyInstaller 빌드

```bash
pyinstaller orbbec.spec
```

- 실행 파일은 `dist/orbbec.exe` (또는 spec에 정의된 이름)에 생성됩니다.
