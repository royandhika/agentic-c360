.PHONY: help setup infra-up infra-down generate backfill reset clean pipeline-build pipeline-up pipeline-down

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
	@echo "  infra-down   Stop simulation containers (preserves volumes/data)"
	@echo "  generate     Run one simulation day (use DATE=YYYY-MM-DD, HOLIDAY=1)"
	@echo "  backfill     Run N simulation days (use DAYS=N, BACKFILL_START=YYYY-MM-DD)"
	@echo "  reset        Wipe simulation state and generated artifacts"
	@echo "  clean        Stop containers, remove volumes, wipe venv + generated data"
	@echo "  pipeline-build  Build Dagster image"
	@echo "  pipeline-up     Start all containers (simulation + pipeline)"
	@echo "  pipeline-down   Stop all containers"

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
	docker compose down -v --remove-orphans 2>/dev/null || true
	rm -rf $(VENV)
	rm -f $(MARKER)
	find simulation -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -f simulation/world/world.db
	rm -f simulation/sources/vendor_api/store/vendor.db
	rm -f simulation/sources/vendor_api/store/vendor.db-wal
	rm -f simulation/sources/vendor_api/store/vendor.db-shm
	rm -f simulation/sources/crm_sftp/tickets/tickets_*.json
	touch simulation/sources/vendor_api/store/.gitkeep
	touch simulation/world/.gitkeep 2>/dev/null || (mkdir -p simulation/world && touch simulation/world/.gitkeep)

pipeline-build: .env
	docker compose -f docker-compose.pipeline.yml build

pipeline-up: .env
	docker compose -f docker-compose.yml -f docker-compose.pipeline.yml up -d

pipeline-down:
	docker compose -f docker-compose.yml -f docker-compose.pipeline.yml down
