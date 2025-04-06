# ---- Dockerfile ----

# 1) Base Image with Python
FROM python:3.9-slim

# 2) Create a working directory for our code
WORKDIR /app

# 3) Install necessary Python packages (Flask)
RUN pip install flask

# 4) Copy the source code into the image
COPY main.py /app/main.py

# 6) Expose port 8880 so Flask can be accessed (Prometheus will scrape http://container:8880/metrics)
EXPOSE 8880

# 7) Define the container's startup command to run our Python script
CMD ["python", "/app/main.py"]
