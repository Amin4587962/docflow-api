# DocFlow API

DocFlow API is an asynchronous document-processing platform built with FastAPI. It handles tasks like document uploading, parsing, processing, and management in a scalable background workflow.

## Features (Current)
- **FastAPI Framework**: Asynchronous and fast endpoints.
- **Dockerized Environment**: Fully containerized API and PostgreSQL setup.
- **Health Check Endpoint**: Verify API-to-database connectivity status in real-time.
- **Secure Configuration**: Environment variables loaded dynamically using Pydantic.

## Tech Stack
- **Backend**: Python 3.11 / FastAPI
- **Database**: PostgreSQL 15
- **Containerization**: Docker / Docker Compose
- **ORM**: SQLAlchemy (Upcoming)

## Prerequisites
Ensure you have the following installed on your machine:
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Git](https://git-scm.com/)

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Amin4587962/docflow-api.git
   cd docflow-api
   ```

2. **Configure Environment Variables:**
   Copy the example environment file and update your credentials:
   ```bash
   cp .env.example .env
   ```
   *Note: `.env` is ignored by Git and will not be pushed to remote repositories.*

3. **Run the Application:**
   Start all services using Docker Compose:
   ```bash
   docker compose up -d --build
   ```

4. **Verify the installation:**
   - **API Health Check**: Access [http://localhost:8000/health](http://localhost:8000/health) to confirm the connection to the database.
   - **Interactive API Documentation**: Explore the Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

## License
[MIT](LICENSE)
