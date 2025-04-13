## 차트 한글 폰트 깨짐 이슈 해결 가이드


### 패키지 업데이트 및 패키지 설치
```bash
sudo apt update
sudo apt install fonts-nanum
```

### 폰트 목록 업데이트 및 matplotlib 캐시 삭제
```bash
sudo fc-cache -fv
rm ~/.cache/matplotlib/fontlist-*.json
```