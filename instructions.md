for redis

- to open wsl terminal write command- "wsl -d Ubuntu"
- to start redis server - "redis-server --daemonize yes --port 6379"
- t check if the redis server has strsted - "redis-cli ping"

for celery setup

- start wsl
- cd backend
- for starting ceelry - "UV_PROJECT_ENVIRONMENT=.wslvenv uv run celery -A src.workers.workers worker --loglevel=info"

for celery beat setup

- start wsl
- cd backend
- for starting ceelry beat - "UV_PROJECT_ENVIRONMENT=.wslvenv uv run celery -A src.workers.workers beat --loglevel=info"

for backend setup

- cd backend
- do "uv sync"
- then "uv run python main.py"

for frontend setup

- cd fronetnd
- npm i not humesha
- npm run serve

for mailhog

- start wsl
- run command - "~/mailhog"
- go to "http://localhost:8025/"
