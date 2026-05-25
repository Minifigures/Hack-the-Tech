.PHONY: install backend frontend dev seed eval test fmt clean

PY := backend/.venv/bin/python
PIP := backend/.venv/bin/pip
UVICORN := backend/.venv/bin/uvicorn

install: install-backend install-frontend

install-backend:
	python3 -m venv backend/.venv
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt

install-frontend:
	npm install

seed:
	$(PY) -m scripts.seed_kb

backend:
	cd backend && ../$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	npm run dev

dev:
	@bash -c 'trap "kill 0" EXIT; \
	  ($(MAKE) backend) & \
	  ($(MAKE) frontend) & \
	  wait'

eval:
	$(PY) -m scripts.run_evals

test-backend:
	$(PY) -m pytest -q tests/backend

test-e2e:
	npx playwright test

test: test-backend test-e2e

fmt:
	$(PY) -m ruff format backend/ scripts/ tests/backend/ || true
	npx prettier --write . || true

clean:
	rm -rf backend/.venv node_modules .next data/evalforge.db data/index.json
