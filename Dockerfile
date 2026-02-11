# Use a lightweight Python base image
FROM python:3.10-slim

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system-level solvers (GLPK and CBC)
RUN apt-get update && apt-get install -y \
    glpk-utils \
    coinor-cbc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first (to leverage caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# This assumes 'WebAPP', 'Classes', and 'Routes' are in the same folder as Dockerfile
COPY . .
RUN chmod -R +x /app/WebAPP/SOLVERs
# Expose the port the app runs on
EXPOSE 5002

# Define the command to run the application
CMD ["python", "API/app.py"]