.PHONY: up build logs

up:
	docker compose up -d --build

build:
	docker compose build

logs:
	docker compose logs -f tfm
