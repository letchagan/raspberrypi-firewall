.PHONY: help install dev test lint format clean run stop logs health

help:
	@echo "Raspberry Pi Firewall & IDPS - Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install dependencies and setup environment"
	@echo "  make dev              Setup development environment with extra tools"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test             Run test suite"
	@echo "  make test-verbose     Run tests with verbose output"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make lint             Run code linting checks"
	@echo "  make format           Format code with Black"
	@echo ""
	@echo "Running:"
	@echo "  make run              Start all IDPS components manually"
	@echo "  make run-dashboard    Start Flask dashboard only"
	@echo "  make run-engine       Start decision engine only"
	@echo "  make run-blockpage    Start block page server only"
	@echo "  make stop             Stop all running components"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs             View IDPS logs"
	@echo "  make logs-dashboard   View dashboard logs"
	@echo "  make logs-engine      View decision engine logs"
	@echo "  make logs-blockpage   View block page logs"
	@echo "  make health           Check system health"
	@echo "  make status           Check systemd service status"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Clean generated files and cache"
	@echo "  make clean-logs       Clean log files"
	@echo "  make clean-cache      Clean Python cache"

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt
	cp .env.example .env
	@echo "✓ Installation complete. Edit .env with your configuration."

dev: install
	. .venv/bin/activate && pip install pytest pytest-cov black flake8

test:
	. .venv/bin/activate && pytest

test-verbose:
	. .venv/bin/activate && pytest -v

test-coverage:
	. .venv/bin/activate && pytest --cov=. --cov-report=html
	@echo "✓ Coverage report generated in htmlcov/index.html"

lint:
	. .venv/bin/activate && flake8 app.py decision_engine.py threat_intel.py utils.py blockpage_server.py config.py

format:
	. .venv/bin/activate && black app.py decision_engine.py threat_intel.py utils.py blockpage_server.py config.py

run:
	@echo "Starting IDPS components..."
	. .venv/bin/activate && sudo -E python3 decision_engine.py &
	. .venv/bin/activate && sudo -E python3 blockpage_server.py &
	. .venv/bin/activate && sudo -E python3 app.py &
	@echo "✓ IDPS components started"

run-dashboard:
	. .venv/bin/activate && sudo -E python3 app.py

run-engine:
	. .venv/bin/activate && sudo -E python3 decision_engine.py

run-blockpage:
	. .venv/bin/activate && sudo -E python3 blockpage_server.py

stop:
	@echo "Stopping IDPS components..."
	sudo pkill -f "python3 app.py" || true
	sudo pkill -f "python3 decision_engine.py" || true
	sudo pkill -f "python3 blockpage_server.py" || true
	@echo "✓ IDPS components stopped"

logs:
	journalctl -u idps.target -f

logs-dashboard:
	journalctl -u idps-dashboard -f

logs-engine:
	journalctl -u idps-decision-engine -f

logs-blockpage:
	journalctl -u idps-blockpage -f

health:
	@echo "=== IDPS Health Check ==="
	@echo "Suricata:"
	@sudo pgrep -a suricata || echo "  ✗ Suricata not running"
	@echo ""
	@echo "nftables:"
	@sudo nft list ruleset > /dev/null 2>&1 && echo "  ✓ nftables OK" || echo "  ✗ nftables error"
	@echo ""
	@echo "Flask Dashboard:"
	@curl -s http://127.0.0.1:3000/api/health | python3 -m json.tool || echo "  ✗ Dashboard not responding"
	@echo ""
	@echo "Block Page Server:"
	@curl -s http://127.0.0.1:5001/ > /dev/null && echo "  ✓ Block page OK" || echo "  ✗ Block page not responding"

status:
	@sudo systemctl status idps.target
	@echo ""
	@sudo systemctl status idps-dashboard
	@echo ""
	@sudo systemctl status idps-decision-engine
	@echo ""
	@sudo systemctl status idps-blockpage

clean: clean-cache clean-logs
	rm -rf htmlcov .pytest_cache .coverage
	@echo "✓ Cache cleaned"

clean-logs:
	rm -f logs/*.log
	@echo "✓ Logs cleaned"

clean-cache:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Python cache cleaned"

.DEFAULT_GOAL := help
