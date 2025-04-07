# Empty or with basic package info
__version__ = "0.1.0"
import subprocess, re
from jinja2 import Environment, FileSystemLoader

def update_readme_section():
    # 1) help 출력
    help_out = subprocess.check_output(
        ["python", "-m", "reposcore", "--help"], text=True
    )
    # 2) 템플릿 렌더링
    env = Environment(loader=FileSystemLoader("."))  # 루트에서 docs 폴더를 찾도록
    tpl = env.get_template("docs/usage.j2")
    rendered = tpl.render(help_output=help_out)
    # 3) README.md 교체
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()
    new = re.sub(r"## Usage[\\s\\S]*?(?=## )", rendered, content)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new)
    print("✅ README Usage 동기화 완료")
