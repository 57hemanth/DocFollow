# Backend

This directory contains the FastAPI backend for the application. It provides a RESTful API for managing patients, appointments, follow-ups, and more.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.10+
- A running MongoDB instance

### Installation

1.  **Navigate to the project root directory**.

2.  **Create and activate a virtual environment:**

    ```bash
    # Create the virtual environment
    python -m venv backend/.venv

    # Activate the virtual environment (Windows)
    .\backend\.venv\Scripts\Activate.ps1

    # Activate the virtual environment (macOS/Linux)
    source backend/.venv/bin/activate
    ```

3.  **Install the required dependencies:**

    Make sure your virtual environment is activated. Then, from the project root directory, run:
    ```bash
    pip install -r backend/requirements.txt
    ```

4.  **Configure Environment Variables**

    The backend uses a MongoDB database. Ensure your instance is running. The connection string is currently hardcoded in `backend/database.py` to connect to `mongodb://localhost:27017`.

### Running the Server

To run the backend server for development, ensure you are in the **project's root directory** and that your virtual environment is activated. Then, execute the following command:

```bash
uvicorn backend.server:app --reload
```

The server will be available at `http://127.0.0.1:8000`. The `--reload` flag enables auto-reloading, so the server will restart automatically when you make changes to the code.

## API Endpoints

Once the server is running, you can access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.

The main resources available are:

-   `/patients`: CRUD operations for patients.
-   `/remainders`: CRUD operations for follow-up reminders.
-   `/followups`: CRUD operations for patient follow-up records.
-   `/appointments`: CRUD operations for appointments.
-   `/settings`: GET and PUT operations for doctor-specific settings.
-   `/webhooks/whatsapp`: Endpoint for receiving incoming WhatsApp messages from Twilio.

### Health Check

There is a health check endpoint to verify that the server is running correctly:

-   `GET /health`: Returns a `200 OK` response with a simple JSON body.
