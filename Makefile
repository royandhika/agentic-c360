.PHONY: help setup infra-up infra-down generate backfill reset clean

help:
	@echo "Usage:"
	@echo "  make setup                  Create venv and install deps"
	@echo "  make infra-up               Start docker-compose services"
	@echo "  make infra-down             Stop docker-compose services"
	@echo "  make generate DATE=...      Generate one retail day"
	@echo "  make backfill DAYS=N        Backfill N days of history"
	@echo "  make reset                  Wipe all generated data"
	@echo "  make clean                  Remove venv"
	@echo ""
	@echo "Examples:"
	@echo "  make setup infra-up"
	@echo "  make generate DATE=2024-08-15"
	@echo "  make generate DATE=2024-04-10 HOLIDAY=1"
	@echo "  make backfill DAYS=365"
	@echo "  make backfill DAYS=90 BACKFILL_START=2024-01-01"
	@echo "  make reset infra-down"

setup:
	@if [ ! -f simulation/.setup-done ]; then \
		echo "Creating venv..."; \
		python3 -m venv simulation/.venv; \
		simulation/.venv/bin/pip install -r simulation/requirements.txt; \
		touch simulation/.setup-done; \
		echo "Setup done."; \
	else \
		echo "Setup already complete (delete simulation/.setup-done to re-run)."; \
	fi

infra-up:
	docker compose up -d
	@echo "Waiting for Postgres to initialize..."
	@sleep 5
	@echo "Infra up. postgres_crm on :5432, mock_ecom_api on :8000"

infra-down:
	docker compose down

DATE ?= $(shell date +%Y-%m-%d)
HOLIDAY ?= 0
generate: setup
	@if [ "$(HOLIDAY)" = "1" ]; then \
		echo "Generating $(DATE) with holiday uplift..."; \
		PYTHONPATH=simulation:simulation/src simulation/.venv/bin/python simulation/scripts/run_day.py --date $(DATE) --holiday; \
	else \
		echo "Generating $(DATE)..."; \
		PYTHONPATH=simulation:simulation/src simulation/.venv/bin/python simulation/scripts/run_day.py --date $(DATE); \
	fi

DAYS ?= 365
BACKFILL_START ?=
backfill: setup
	@if [ "$(HOLIDAY)" = "1" ]; then \
		if [ -n "$(BACKFILL_START)" ]; then \
			PYTHONPATH=simulation:simulation/src simulation/.venv/bin/python simulation/scripts/backfill.py --days $(DAYS) --start $(BACKFILL_START) --holiday; \
		else \
			PYTHONPATH=simulation:simulation/src simulation/.venv/bin/python simulation/scripts/backfill.py --days $(DAYS) --holiday; \
		fi; \
	else \
		if [ -n "$(BACKFILL_START)" ]; then \
			PYTHONPATH=simulation:simulation/src simulation/.venv/bin/python simulation/scripts/backfill.py --days $(DAYS) --start $(BACKFILL_START); \
		else \
			PYTHONPATH=simulation:simulation/src simulation/.venv/bin/python simulation/scripts/backfill.py --days $(DAYS); \
		fi; \
	fi

reset:
	bash simulation/scripts/reset.sh

clean:
	rm -rf simulation/.venv simulation/.setup-done
	@echo "Cleaned venv and setup marker."
