# Use an official Python image as the base
FROM python:3.12.6-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the requirements.txt file to the container
COPY requirements.txt ./

# Install the dependencies listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Ensure the MariaDB client library is available if needed
RUN apt-get update && \
    apt-get install -y default-libmysqlclient-dev gcc && \
    pip install mysqlclient && \
    apt-get remove -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Expose port 8050 for Dash to be accessible
EXPOSE 8050

# Set the environment variable to disable Dash debug mode
ENV DASH_DEBUG_MODE False

# Command to start the application
CMD ["python", "app.py"]
