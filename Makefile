MDLINT ?= markdownlint-cli2
NIXIE ?= nixie
MDFORMAT_ALL ?= mdformat-all
export PATH := $(HOME)/.local/bin:$(HOME)/.bun/bin:$(PATH)
UV ?= $(shell command -v uv 2>/dev/null || printf '%s/.local/bin/uv' "$$HOME")
USER_CARGO := $(HOME)/.cargo/bin/cargo
USER_WHITAKER := $(HOME)/.local/bin/whitaker
USER_BIN_PATH := $(HOME)/.cargo/bin:$(HOME)/.local/bin:$(HOME)/.bun/bin
TOOLS = $(MDFORMAT_ALL) $(MDLINT)
VENV_TOOLS = pytest
UV_ENV = PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools
TYPOS_CONFIG_BUILDER_VERSION ?= v0.1.1
TYPOS_CONFIG_BUILDER = env $(UV_ENV) $(UV) tool run --from \
	"git+https://github.com/leynos/typos-config-builder.git@$(TYPOS_CONFIG_BUILDER_VERSION)" \
	typos-config-builder
WITH_ACT ?= 0
ACT_TEST_ENV = $(if $(filter 1 true yes on,$(WITH_ACT)),RUN_ACT_VALIDATION=1,)
PYTEST_XDIST_WORKERS ?= auto
PYTHON_TARGETS ?= setwork tests
# uv's PyPy 3.12.14 release provides PyPy 8.0.0; verify both identities.
PYLINT_PYTHON ?= pypy@3.12.14
PYLINT_VERSION ?= 4.0.9
PYLINT_TARGETS ?= $(PYTHON_TARGETS)
ASTROID_VERSION ?= 4.0.4
PYLINT_CACHE ?= .cache/pylint/pypy312
DF12_PYLINT_CACHE ?= .cache/pylint/cpython314
PYLINT_TOOL = PYLINTHOME=$(PYLINT_CACHE) $(UV_ENV) $(UV) tool run \
	--managed-python --python $(PYLINT_PYTHON) --from 'pylint==$(PYLINT_VERSION)' \
	--with 'astroid==$(ASTROID_VERSION)'
PYLINT = $(PYLINT_TOOL) python -m pylint --jobs=1
# Keep the DF12 policy pass isolated from the classic PyPy environment.
DF12_PYTHON_LINTS_REF ?= v0.3.0
DF12_PYTHON_LINTS = git+https://github.com/leynos/df12-python-lints.git@$(DF12_PYTHON_LINTS_REF)
DF12_PYTHON ?= cpython@3.14
DF12_PYLINT_TARGETS ?= $(PYTHON_TARGETS)
DF12_PYLINT_MESSAGES = R9101,C9102,R9103,R9104,C9105,C9106,C9107,R9108,R9109,R9110,R9111,C9112,R9112
DF12_PYLINT_TOOL = PYLINTHOME=$(DF12_PYLINT_CACHE) $(UV_ENV) $(UV) tool run \
	--managed-python --python $(DF12_PYTHON) --from 'pylint==$(PYLINT_VERSION)' \
	--with 'astroid==$(ASTROID_VERSION)' --with '$(DF12_PYTHON_LINTS)'
DF12_PYLINT = $(DF12_PYLINT_TOOL) python -m pylint --jobs=1 \
	--disable=all --load-plugins=df12_python_lints \
	--enable=syntax-error,$(DF12_PYLINT_MESSAGES)


.PHONY: help all audit clean build build-release lint lint-python fmt check-fmt \
        markdownlint nixie spelling test typecheck verify-classic-pylint \
        verify-df12-pylint $(TOOLS) $(VENV_TOOLS)

.DEFAULT_GOAL := all

all: build check-fmt lint typecheck test
	+$(MAKE) spelling

define ensure_uv
	@command -v $(UV) >/dev/null 2>&1 || { \
	  printf "Error: uv is required, but '%s' was not found or is not executable\n" "$(UV)" >&2; \
	  exit 1; \
	}
endef

.venv: pyproject.toml
	$(call ensure_uv)
	$(UV_ENV) $(UV) venv --clear

build: .venv ## Build virtual-env and install deps
	$(UV_ENV) $(UV) sync --group dev

build-release: ## Build artefacts (sdist & wheel)
	$(call ensure_uv)
	$(UV_ENV) $(UV) run python -m build --sdist --wheel

clean: ## Remove build artefacts
	rm -rf build dist *.egg-info \
	  .mypy_cache .pytest_cache .coverage coverage.* \
	  lcov.info htmlcov .venv .uv-cache .uv-tools \
	  .typos-oxendict-base.json .typos-oxendict-base.toml
	find . -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf

define ensure_tool
	@command -v $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required, but not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

define ensure_tool_venv
	@$(UV_ENV) $(UV) run which $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required in the virtualenv, but is not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

ifneq ($(strip $(TOOLS)),)
$(TOOLS): ## Verify required CLI tools
	$(call ensure_tool,$@)
endif


ifneq ($(strip $(VENV_TOOLS)),)
.PHONY: $(VENV_TOOLS)
$(VENV_TOOLS): build ## Verify required CLI tools in venv
	$(call ensure_tool_venv,$@)
endif


fmt: build $(MDFORMAT_ALL) ## Format sources
	$(UV_ENV) $(UV) run ruff format $(PYTHON_TARGETS)
	$(UV_ENV) $(UV) run ruff check --select I --fix $(PYTHON_TARGETS)

	$(MDFORMAT_ALL)

check-fmt: build ## Verify formatting
	$(UV_ENV) $(UV) run ruff format --check $(PYTHON_TARGETS)

	# mdformat-all doesn't currently do checking

lint: lint-python ## Run linters

verify-classic-pylint: ## Verify PyPy 8.0.0 with Python 3.12 before linting
	$(PYLINT_TOOL) python -c 'import sys; expected = ("pypy", (3, 12), (8, 0, 0)); actual = (sys.implementation.name, sys.version_info[:2], getattr(sys, "pypy_version_info", ())[:3]); assert actual == expected, f"classic pylint requires {expected}, got {actual}"; print(sys.version)'

verify-df12-pylint: ## Verify CPython 3.14 before running DF12 lints
	$(DF12_PYLINT_TOOL) python -c 'import sys; expected = ("cpython", (3, 14)); actual = (sys.implementation.name, sys.version_info[:2]); assert actual == expected, f"DF12 pylint requires {expected}, got {actual}"; print(sys.version)'

lint-python: build verify-classic-pylint verify-df12-pylint ## Run Python linters
	$(UV_ENV) $(UV) run ruff check $(PYTHON_TARGETS)
	$(UV_ENV) $(UV) run interrogate --fail-under 100 $(PYTHON_TARGETS)
	$(PYLINT) $(PYLINT_TARGETS)
	$(DF12_PYLINT) $(DF12_PYLINT_TARGETS)


typecheck: build ## Run typechecking
	$(UV_ENV) $(UV) run ty --version
	$(UV_ENV) $(UV) run ty check $(PYTHON_TARGETS)

audit: build ## Audit dependencies for known vulnerabilities
	$(UV_ENV) $(UV) run pip-audit


markdownlint: $(MDLINT) ## Lint Markdown files and spelling
	env -u NO_COLOR $(MDLINT) '**/*.md'
	+$(MAKE) spelling

spelling: ## Enforce en-GB-oxendict spelling
	$(TYPOS_CONFIG_BUILDER) gate --repository .

nixie: ## Validate Mermaid diagrams
	$(call ensure_tool,$(NIXIE))
	$(NIXIE) --no-sandbox

test: build $(VENV_TOOLS) ## Run tests
	$(UV_ENV) $(ACT_TEST_ENV) $(UV) run pytest -v -n $(PYTEST_XDIST_WORKERS)


help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS=":.*##"; printf "Available targets:\n"} {gsub(/^[[:space:]]+/, "", $$2); printf "  %-20s %s\n", $$1, $$2}'
