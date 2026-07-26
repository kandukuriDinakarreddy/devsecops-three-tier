FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -u 1000 appuser && chown -R appuser /app
USER appuser
EXPOSE 5000
CMD ["python", "app.py"]