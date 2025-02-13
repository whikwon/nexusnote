# NexusNote - Backend

NexusNote is the backend service for the NexusNote application. This document provides instructions on how to install and run the server in both development and production environments.

## Prerequisites

Before proceeding, ensure that you have the following installed:

- [uv](https://docs.astral.sh/uv/getting-started/installation/) – A necessary tool for syncing resources.
- [ollama](https://ollama.com) - Required for local LLM, embedding models.
- [MongoDB](https://www.mongodb.com/docs/manual/installation/) - Required for database operations.
- Python (version 3.10 or higher) and the required dependencies for FastAPI.

## Installation

After installing uv, run the following command to synchronize resources:

```
uv sync
```

## Running the Application

### Development Mode

For development, you can run the FastAPI server with auto-reload enabled. This allows the server to automatically restart whenever you make changes to the code:

```
fastapi run --reload app/main.py
```

- Server URL: http://localhost:8000
- Swagger Documentation: http://localhost:8000/docs

## Production Mode

To run the application in a production environment, use Gunicorn with the provided configuration file:

```
gunicorn -c gunicorn_conf.py main:app
```

This command will start the application using Gunicorn, which is well-suited for production deployments.

## Additional Resources

For further information and examples, consider reviewing the following references:

- [FastAPI with MongoDB Example by Youngestdev](https://github.com/Youngestdev/fastapi-mongo)
- [Full-Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template)
- [Handling Errors in FastAPI](https://fastapi.tiangolo.com/tutorial/handling-errors/#reuse-fastapis-exception-handlers)
