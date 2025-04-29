# Use an official Python image as the base
FROM python:3.12.6-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the requirements.txt file to the container
COPY requirements.txt ./

# Install system dependencies required for mysqlclient
RUN apt-get update && \
    apt-get install -y gcc default-libmysqlclient-dev pkg-config && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code to the container
COPY . .

# Expose port 8050 for Dash to be accessible
EXPOSE 8050

# Set the environment variable to disable Dash debug mode
ENV DASH_DEBUG_MODE=false

# Command to start the application
CMD ["python", "app.py"]