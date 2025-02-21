FROM python:3.10

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .

# Install any dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port the app will run on (if applicable)
EXPOSE 8000

# Define the command to run the application
CMD ["python", "main.py"]
