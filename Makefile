.PHONY: help setup generate backfill generator-reset generator-clean generator-up generator-down orchestrator-up orchestrator-down orchestrator-reset orchestrator-clean dbt-parse dbt-debug dbt-run dbt-test dbt-build

ORCHESTRATOR_FILE = docker-compose.orchestrator.yml
DBT_SERVICE = dagster-webserver
DBT_PROJECT = /opt/dagster/dbt
DBT_PROFILES = /opt/dagster/ops
DBT_ARGS = --project-dir $(DBT_PROJECT) --profiles-dir $(DBT_PROFILES)

-include .env
export

VENV = simulation/.venv
MARKER = simulation/.setup-done

help: ## Show this help
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  setup        		Create venv, install deps, init dbt profiles"
	@echo "  generator-up		Start mock source containers (docker compose up)"
	@echo "  generate    		Run one simulation day (use DATE=YYYY-MM-DD, HOLIDAY=1)"
	@echo "  backfill     		Run N simulation days (use DAYS=N, BACKFILL_START=YYYY-MM-DD)"
	@echo "  generator-reset 	Wipe simulation state and generated artifacts"
	@echo "  generator-clean 	Stop generator, remove volumes, wipe venv + generated data"
	@echo "  generator-down		Stop generator containers (preserves volumes/data)"
	@echo "  orchestrator-up  	Start orchestrator containers (requires generator up)"
	@echo "  orchestrator-down	Stop orchestrator containers"
	@echo "  orchestrator-reset	Wipe Dagster run storage, dbt target/logs"
	@echo "  orchestrator-clean	Stop orchestrator, wipe Dagster/dbt/CH volumes"
	@echo "  dbt-parse      	Compile dbt manifest (run inside dagster container)"
	@echo "  dbt-debug      	Check dbt connections (run inside dagster container)"
	@echo "  dbt-run        	Run dbt models (run inside dagster container)"
	@echo "  dbt-test       	Run dbt tests (run inside dagster container)"
	@echo "  dbt-build      	dbt build = run + test (run inside dagster container)"

.env:
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
	fi

setup: $(MARKER) .env
	@if [ ! -f ops/profiles.yml ]; then \
		echo "Creating ops/profiles.yml from ops/profiles.yml.example..."; \
		cp ops/profiles.yml.example ops/profiles.yml; \
	fi
	@test -f ops/profiles.yml || { echo "ERROR: ops/profiles.yml still missing!"; exit 1; }
	@echo "==> dbt config OK"

$(MARKER): simulation/requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r simulation/requirements.txt
	touch $(MARKER)

generator-up: .env
	docker compose up -d --build

generator-down:
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

generator-reset:
	bash simulation/scripts/reset.sh

generator-clean:
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

orchestrator-up: generator-up
	docker compose -f docker-compose.orchestrator.yml up -d --build

orchestrator-down:
	docker compose -f docker-compose.orchestrator.yml down

orchestrator-reset:
	@echo "Wiping Dagster run storage + dbt cache..."
	docker compose -f $(ORCHESTRATOR_FILE) run --rm --no-deps $(DBT_SERVICE) \
		sh -c "rm -rf /opt/dagster/dagster_pipeline/dagster_home/storage /opt/dagster/dagster_pipeline/dagster_home/logs /opt/dagster/dagster_pipeline/dagster_home/.logs_queue /opt/dagster/dbt/target /opt/dagster/dbt/logs /opt/dagster/dagster_pipeline/dagster_pipeline/__pycache__ /opt/dagster/dagster_pipeline/dagster_pipeline/assets/__pycache__"
	@echo "Orchestrator cache + logs wiped."

orchestrator-clean:
	@echo "Wiping orchestrator artifacts + volumes..."
	-docker compose -f $(ORCHESTRATOR_FILE) run --rm --no-deps $(DBT_SERVICE) \
		sh -c "rm -rf /opt/dagster/dagster_pipeline/dagster_home/storage /opt/dagster/dagster_pipeline/dagster_home/logs /opt/dagster/dagster_pipeline/dagster_home/.logs_queue /opt/dagster/dbt/target /opt/dagster/dbt/logs /opt/dagster/dagster_pipeline/dagster_pipeline/__pycache__ /opt/dagster/dagster_pipeline/dagster_pipeline/assets/__pycache__" 2>/dev/null
	-docker compose -f $(ORCHESTRATOR_FILE) down -v 2>/dev/null
	@echo "Orchestrator cleaned."

dbt-parse:
	@echo "Compiling dbt manifest..."
	docker compose -f $(ORCHESTRATOR_FILE) exec -T $(DBT_SERVICE) \
		dbt parse $(DBT_ARGS)

dbt-debug:
	@echo "Running dbt debug..."
	docker compose -f $(ORCHESTRATOR_FILE) exec -T $(DBT_SERVICE) \
		dbt debug $(DBT_ARGS)

dbt-run:
	@echo "Running dbt run..."
	docker compose -f $(ORCHESTRATOR_FILE) exec -T $(DBT_SERVICE) \
		dbt run $(DBT_ARGS)

dbt-test:
	@echo "Running dbt test..."
	docker compose -f $(ORCHESTRATOR_FILE) exec -T $(DBT_SERVICE) \
		dbt test $(DBT_ARGS)

dbt-build:
	@echo "Running dbt build..."
	docker compose -f $(ORCHESTRATOR_FILE) exec -T $(DBT_SERVICE) \
		dbt build $(DBT_ARGS)
