.PHONY: run shell test migrate migrations static createsuperuser lint check clean

VENV := myworld/bin
PY   := $(VENV)/python
PIP  := $(VENV)/pip

run:
	$(PY) manage.py runserver

shell:
	$(PY) manage.py shell

test:
	$(PY) manage.py test apps

migrate:
	$(PY) manage.py migrate

migrations:
	$(PY) manage.py makemigrations

static:
	$(PY) manage.py collectstatic --noinput

createsuperuser:
	$(PY) manage.py createsuperuser

check:
	$(PY) manage.py check

lint:
	$(VENV)/flake8 apps --max-line-length=110 --exclude=migrations

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -name "*.pyc" -delete 2>/dev/null; \
	rm -rf staticfiles/ .coverage; \
	echo "done"
