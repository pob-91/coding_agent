.PHONY: build
build:
	docker build --no-cache -t coding-agent:latest .

.PHONY: up
up:
	docker compose --profile dev up -d

.PHONY: up-all
up-all:
	docker compose --profile test up -d

.PHONY: down
down:
	docker compose --profile dev down -v

.PHONY: down-all
down-all:
	docker compose --profile test down -v

.PHONY: trash
trash:
	docker compose down -v --rmi all

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build          - Build the Docker image without cache"
	@echo "  up             - Start services in detached mode"
	@echo "  down           - Stop and remove containers and networks"
	@echo "  trash          - Remove everything (containers, networks, volumes, images)"
	@echo "  help           - Show this help message"
