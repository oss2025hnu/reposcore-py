.PHONY: test lint readme pre-commit clean

PYTHON_MODULES := reposcore

VENV := .venv
VIRTUALENV := -m venv

DEFAULT_PYTHON := $(shell which python3)
PYTHON := env PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

VERSION := $(shell grep '__version__' reposcore/__init__.py |cut -d'"' -f 2)
DISTRO := $(shell lsb_release -si)

version:
	@echo $(VERSION)

venv:
	test -d $(VENV) || $(DEFAULT_PYTHON) $(VIRTUALENV) $(VENV)

requirements: venv
	$(PIP) install -r requirements.txt -r requirements-dev.txt

test: requirements
	$(PYTEST) tests

update-fonts: requirements
	@echo "Updating fonts cache..."
	sudo fc-cache -fv
	$(PYTHON) -c "import shutil; import matplotlib; shutil.rmtree(matplotlib.get_cachedir())"

install-fonts:
	@echo "🔍 Detecting system..."
	@if [ "$$(uname)" = "Darwin" ]; then \
		echo "🍎 macOS detected. Installing NanumGothic via Homebrew..."; \
		brew tap homebrew/cask-fonts && brew install --cask font-nanum-gothic; \
	elif [ -f /etc/debian_version ]; then \
		echo "🐧 Debian/Ubuntu detected. Installing fonts-nanum..."; \
		sudo apt update && sudo apt install -y fonts-nanum; \
	else \
		echo "⚠️ Unsupported OS. Please install a Korean font (NanumGothic) manually."; \
	fi

ifneq (,$(filter $(DISTRO),Debian Ubuntu))
	@echo "Installing Noto Sans CJK fonts for Debian..."
	sudo apt-get update -y
	sudo apt-get install -y fonts-noto-cjk

else ifneq (,$(filter $(DISTRO),RedHat Fedora RHEL CentOS Rocky))
	@echo "Installing Noto Sans CJK fonts for RedHat..."
	sudo dnf install -y google-noto-sans-cjk-fonts

else ifneq (,$(filter $(DISTRO),SUSE openSUSE))
	@echo "Installing Noto Sans CJK fonts for SUSE..."
	sudo zypper install -y noto-sans-cjk-fonts

else ifneq (,$(filter $(DISTRO),Arch Manjaro))
	@echo "Installing Noto Sans CJK fonts for Arch..."
	sudo pacman -Sy --noconfirm noto-fonts-cjk

else ifneq (,$(filter $(DISTRO),Gentoo))
	@echo "Installing Noto Sans CJK fonts for Gentoo..."
	sudo emerge -y media-fonts/noto-cjk

else ifneq (,$(filter $(DISTRO),Alpine))
	@echo "Installing Noto Sans CJK fonts for Alpine..."
	sudo apk add --no-cache font-noto-cjk

else
	@echo "Unsupported distribution: $(DISTRO)"
	@echo "Please install Noto Sans CJK fonts manually"
	@exit 1
endif

# README 동기화
readme: README.md

# README 자동 생성
README.md: template_README.md scripts/generate_readme.py reposcore/__main__.py
	python scripts/generate_readme.py

# PR 전에 자동으로 README 검증
pre-commit: readme

# 불필요한 파일 정리
clean:
	@if [ -d "$(VENV)" ]; then \
		echo ".venv 가상 환경을 삭제합니다..."; \
		rm -rf $(VENV); \
	fi
	@if [ -d "results" ]; then \
		echo "results 디렉토리를 삭제합니다..."; \
		rm -rf results; \
	fi
