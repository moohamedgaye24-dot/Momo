# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create the traces and models directories
RUN mkdir -p traces models

# Run paper_trading.py when the container launches
CMD ["python", "-u", "paper_trading.py"]
