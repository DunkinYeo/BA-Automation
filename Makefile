PYTHON  := $(shell [ -f .venv/bin/python ] && echo .venv/bin/python || echo python3)
CONFIG  ?= config/bioarmour.yaml
RESULT  ?= output/result.json

.PHONY: install run clean-output help

help:
	@echo ""
	@echo "  BioArmour Regression Automation"
	@echo ""
	@echo "  make install       — 최초 1회: 가상환경 + 패키지 설치"
	@echo "  make run           — 전체 regression 실행 (Phase 1~4)"
	@echo "  make clean-output  — output/ 정리"
	@echo ""
	@echo "  옵션:"
	@echo "  make CONFIG=config/other.yaml run       — config 파일 지정"
	@echo "  make RESULT=output/my.json run           — JSON 결과 저장 경로 지정"
	@echo ""

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip -q
	$(PYTHON) -m pip install -r requirements.txt -q
	@echo ""
	@echo "  설치 완료. 'make run' 으로 실행하세요."
	@echo ""

run:
	PYTHONPATH=. $(PYTHON) src/main.py --config $(CONFIG) --result-json $(RESULT)

clean-output:
	rm -rf output/*
	@echo "  output/ 정리 완료."
