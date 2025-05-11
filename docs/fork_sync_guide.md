# fork_sync_guide.md

이 문서는 Python 기반 프로젝트에서 GitHub 포크(fork) 저장소를 원본 저장소(upstream)와 **동기화(sync)** 하는 방법에 대해 설명합니다.  
Python 개발 환경에서는 종종 오픈소스를 포크하여 개발을 이어가게 되며,  
원본 저장소의 변경 사항을 주기적으로 반영하지 않으면 커밋 충돌 및 버전 불일치 문제가 발생할 수 있습니다.

---

## 🧭 기본 개념

- **origin**: 내 GitHub 계정에 있는 포크 저장소
- **upstream**: 원본 저장소 (포크 대상)
- **동기화 목적**: 원본 저장소의 최신 커밋 및 Python 코드 변경사항을 내 저장소에도 반영

---

## ✅ CLI 기반 동기화 방법 (추천)

### 1. 로컬 저장소 클론
```bash
git clone https://github.com/내계정명/포크저장소.git
cd 포크저장소
```

### 2. 원본 저장소를 upstream으로 등록
```bash
git remote add upstream https://github.com/원본계정명/원본저장소.git
```

### 3. 등록 확인
```bash
git remote -v
```

### 4. 원본 저장소의 변경사항 가져오기
```bash
git fetch upstream
```

### 5. 내 브랜치(main)에 병합
```bash
git checkout main
git merge upstream/main
```

또는 최신 이력을 깔끔히 정리하려면 rebase 사용
```bash
git rebase upstream/main
```

### 6. 내 GitHub 저장소(origin)에 푸시
```bash
git push origin main
```

---

## 🔄 GitHub 웹에서 동기화하기 (GUI 방식)

1. GitHub에서 내 포크 저장소로 이동
2. 상단에 있는 `Sync fork` 버튼 클릭
3. 자동으로 최신 커밋 반영됨

> 충돌이 발생할 경우 수동 병합 필요

---

## ⚠️ Python 프로젝트에서의 주의사항

- `requirements.txt`, `pyproject.toml` 등의 변경사항이 upstream에서 발생했을 경우, 반드시 pull 후 로컬 가상환경도 재설정할 것
- 충돌 방지를 위해 자주 `fetch`하고 변경사항을 로컬에서 테스트한 후 push 권장
- `venv`, `.env`, `__pycache__/` 등은 `.gitignore`로 관리되어야 하며, 충돌에 영향을 주지 않도록 유의

---

## 📌 요약 명령어

```bash
git remote add upstream [원본 URL]
git fetch upstream
git merge upstream/main
git push origin main
```

---

이 가이드는 Python 기반 프로젝트에서 포크 저장소를 원본 저장소와 지속적으로 동기화하여,  
협업 시 충돌을 줄이고 최신 코드 흐름을 유지하는 데 도움을 줍니다.
