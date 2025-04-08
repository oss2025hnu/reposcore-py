# GitHub 토큰 발급 방법

GitHub 토큰(Personal Access Token)은 비밀번호 대신 사용하여 GitHub API에 접근하거나 Git 작업을 인증할 수 있는 문자열입니다. 비밀번호보다 안전하며, 특정 범위의 권한만 부여하고 만료 기간을 설정할 수 있어 유용합니다.

다음은 GitHub 토큰을 발급하는 방법입니다.

# 1. GitHub 설정 페이지 접근
- [GitHub 웹사이트](https://github.com/)에 로그인 합니다.
 - 우측 상단의 프로필 사진을 클릭합니다.
 - 드롭다운 메뉴에서 **Settings** 을 클릭합니다.

    ![Click settings](images/settings.png)

# 2. 개발자 설정 메뉴 접근
- 좌측 사이드바에서 가장 아래쪽에 있는 **Developer settings** 을 클릭합니다.
        
   ![Click Developer settings](images/developer-settings.png)

# 3. Personal access tokens (개인 접근 토큰) 메뉴 접근
- 좌측 사이드바에서 **Personal access tokens > Tokens (classic)** 을 클릭합니다.
    
   ![token classic](images/token-classic.png)

# 4. 새로운 토큰 생성
 - 우측 상단의 **Generate new token (classic)** 버튼을 클릭합니다.
    
    ![generate new token](images/generate-new-token.png)

# 5. 깃허브 계정 비밀번호 입력
 - 비밀번호를 입력해 본인의 계정임을 확인한다.

   ![confirm access](images/confirm-access.png)

# 6. 토큰 이름 및 권한 부여
- `Note` 토큰의 이름을 입력한다.
 - `Expiration` 토큰의 유효기간을 정한다.
 - `Select scopes` 허가한 권한을 설정한다.
        - 현재 프로젝트에 실행하기 위해 필요한 권한은 없으므로 해당 부분은 넘어가도 된다.
    ![oss2025hn](images/oss2025hnu.png) 

# 7. 토큰 생성
 - 토큰 생성 화면에서 스크롤을 아래로 내려 **Generate token** 버튼을 클릭한다.
 ![generate token](images/generate-token.png)
 - 이후 **Personal access tokens (classic)** 화면으로 돌아오며, 화면에 보이는 토큰값을 복사하면된다.
 ![copy token](images/copy-token.png)

# 8. 사용 예시
GitHub API를 호출할 때 Personal Access Token을 사용하는 간단한 예시입니다.

```python
import requests

# GitHub Personal Access Token
token = "your_personal_access_token"

# 리포지토리 경로 설정
repo_owner = "your_repo_owner"  # 예: 'oss2025hnu'
repo_name = "your_repo_name"    # 예: 'reposcore-py'
repo_path = f"{repo_owner}/{repo_name}"  # 리포지토리 경로

# 페이지 번호와 한 페이지에 가져올 이슈 개수
page = 1
per_page = 30

while True:
    # API 요청 URL 설정
    url = f"https://api.github.com/repos/{repo_path}/issues"

    # GET 요청 보내기
    response = requests.get(url,
                            auth=('your_username', token),  # 사용자 이름과 토큰으로 인증
                            params={
                                'state': 'all',  # 모든 상태의 이슈 불러오기
                                'per_page': per_page,  # 한 페이지에 30개 이슈
                                'page': page        # 페이지 번호
                            })
    
    # 응답 처리
    if response.status_code == 200:
        issues = response.json()
        if not issues:  # 이슈가 더 이상 없으면 종료
            break
        print(f"Page {page} 이슈 목록:", issues)
        page += 1  # 다음 페이지로 이동
    else:
        print("오류 발생:", response.status_code)
        break
```
