# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /code

# Copy requirements file
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application source code
COPY ./app /code/app

# Start the application with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
