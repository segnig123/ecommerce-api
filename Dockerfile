# Use Python 3.14 lightweight Linux image
FROM python:3.14-slim

# Python settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root application user
RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --create-home appuser

# Switch to non-root user
USER appuser

# Copy application files with correct ownership
COPY --chown=appuser:appgroup . .

# Run application as non-root user
USER appuser

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]