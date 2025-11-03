# Python command paths
PYTHON:=$(shell command -v python3 2>/dev/null || command -v python)
PIP:=$(shell command -v pip3 2>/dev/null || command -v pip 2>/dev/null || echo "$(PYTHON) -m pip")
PYINSTALLER:=$(shell command -v pyinstaller 2>/dev/null || echo "$(PYTHON) -m PyInstaller")

# Parameters
ARCH_FLAGS?=
PROJECT?=canipy
SRC=main.py
REQS?=requirements.txt

# If rebuilding, overrides if dependencies are to not be re-processed
SKIP_DEPS?=0

# Just build when "make" is run
build:
	@echo "Packaging CaniPy..."
	$(PYINSTALLER) --onefile --noconsole $(ARCH_FLAGS) -n $(PROJECT) $(SRC)

# Installs dependencies
deps:
	@echo "Installing dependencies..."
	$(PIP) install --upgrade -r $(REQS)

# Dependnecies then build if "make all"
all: deps build

# Clean
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf dist/ build/ $(PROJECT).spec

# Re-package project
rebuild: clean
ifeq ($(SKIP_DEPS),0)
	$(MAKE) deps
endif
	$(MAKE) build