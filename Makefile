.PHONY: help setup infra-up infra-down generate backfill reset clean

-include .env
export

VENV = simulation/.venv
MARKER = simulation/.setup-done

help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  setup        Create venv and install Python dependencies"
	@echo "  infra-up     Start mock source containers (docker compose up)"
	@echo "  infra-down   Stop mock source containers (docker compose down)"
	@echo "  generate     Run one simulation day (use DATE=YYYY-MM-DD, HOLIDAY=1)"
	@echo "  backfill     Run N simulation days (use DAYS=N, BACKFILL_START=YYYY-MM-DD)"
	@echo "  reset        Wipe simulation state and generated artifacts"
	@echo "  clean        Remove venv, marker, and __pycache__ dirs"

.env:
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
	fi

setup: $(MARKER) .env

$(MARKER): simulation/requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r simulation/requirements.txt
	touch $(MARKER)

infra-up: .env
	docker compose up -d

infra-down:
	docker compose down

generate: $(MARKER) .env
	$(VENV)/bin/python simulation/scripts/run_day.py \
		--date $(or $(DATE),$(shell date '+%Y-%m-%d')) \
		$(if $(HOLIDAY),--holiday)

backfill: $(MARKER) .env
	$(VENV)/bin/python simulation/scripts/backfill.py \
		--days $(or $(DAYS),30) \
		$(if $(BACKFILL_START),--start $(BACKFILL_START)) \
		$(if $(HOLIDAY),--holiday)

reset:
	bash simulation/scripts/reset.sh

clean:
	rm -rf $(VENV)
	rm -f $(MARKER)
	rm -rf simulation/gen/__pycache__
	rm -rf simulation/lib/__pycache__
	rm -rf simulation/world/__pycache__
	rm -rf simulation/scripts/__pycache__
	rm -rf simulation/sources/vendor_api/__pycache__ 2>/dev/null || true
	sudo rm -rf simulation/sources/vendor_api/__pycache__ 2>/dev/null || true
