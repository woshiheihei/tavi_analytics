FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

# Workdir inside the container
WORKDIR /app

# Install Python dependencies first (leverage Docker layer cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy server source code
COPY . /app

# Default runtime environment
ENV PORT=8080 \
	PDF_OUT_DIR=/app/out

# Prepare output directory and set permissions for non-root user
RUN mkdir -p /app/out \
	&& chown -R pwuser:pwuser /app

# Drop privileges for runtime
USER pwuser

EXPOSE 8080

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

