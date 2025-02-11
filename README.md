# NexusNote - Backend

## Installation

```
uv sync
```

## Run

```
fastapi run --reload app/main.py
```

```
gunicorn -c gunicorn_conf.py main:app
```

## References

- https://github.com/Youngestdev/fastapi-mongo
- https://github.com/fastapi/full-stack-fastapi-template
- https://fastapi.tiangolo.com/tutorial/handling-errors/#reuse-fastapis-exception-handlers
