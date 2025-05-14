# Cherry-Pick
> 다른 브랜치에 있는 커밋 중 **원하는 것만 골라 현재 브랜치에 적용**할 수 있는 명령어
> 커밋 단위로 기능을 분리하거나, 특정 기능만 따로 이동하고 싶을 때 사용

## 사용법

### CLI를 사용하여 # Cherry-Pick 사용하기
1. 새 브랜치 만들고 그 상태로 이동
``` bash
git checkout -b {Commit을 가져올 브랜치}
```
2. 커밋 ID 확인
```bash
git log --oneline
```
3. 특정 커밋을 현재 브랜치에 적용(복사하기)
- 가져올 commit이 하나인 경우
``` bash
git cherry-pick {커밋 ID}
```
- 가져올 commit이 연속적일 경우
``` bash
git cherry-pick {시작 커밋 ID}^..{종료 커밋 ID}
```
^를 붙여 마지막 커밋까지 가져오도록 함.
- merge commit에 대해 cherry-pick 할 경우
```bash
git cherry-pick -m 1 {머지할 커밋 ID}
```
-m 1 옵션은 병합 커밋의 어느 부모를 기준으로 삼을지 의미
일반적으로 '1'은 기본 브랜치(main 등) 의미
---
### GUI를 사용하여 cherry-pick 사용하기
[커밋 cherry-pick 깃허브 공식 문서 참고](https://docs.github.com/ko/enterprise-cloud@latest/desktop/managing-commits/cherry-picking-a-commit-in-github-desktop)


## cherry-Pick 시 충돌 해결법
다 브랜치로부터 특정 커밋을 복사해올 때 현재 브랜치와의 코드버전이 맞지 않아 충돌이 일어나는 경우가 있음
1. 충돌 난 코드 수정
2. 충돌 해결된 파일을 staging
```bash
git add {충돌난 파일 경로}
```
3. cherry-pick 이어서서 진행
```bash
git cherry-pick --continue
```

- cherry-pick 중단
```bash
git cherry-pick -–abort
```