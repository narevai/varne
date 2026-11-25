.PHONY: install format check test dev debug

install:
	@requirements=$$(mktemp) && \
		trap 'rm -f "$$requirements"' EXIT && \
		uv export --locked --no-hashes --no-emit-project --output-file "$$requirements" --quiet && \
		uv pip install --system -r "$$requirements" -e .

format:
	ruff format src tests
	ruff check src tests --fix

check:
	ruff format --check src tests
	ruff check src tests
	python -m basedpyright src tests --pythonpath "$$(python -c 'import sys; print(sys.executable)')"

debug:
	ENVIRONMENT=development DEBUG=true LOG_LEVEL=DEBUG python -m pdb -m varne.app

test:
	pytest --record-mode=none --block-network

dev:
	ENVIRONMENT=development DEBUG=false LOG_LEVEL=DEBUG python -m varne.app

vcr-record:
	infisical run -- pytest --record-mode=new_episodes

vcr-record-rewrite:
	infisical run -- pytest --record-mode=rewrite

vcr-format:
	./scripts/vcr-format.sh

vcr: vcr-record vcr-format
