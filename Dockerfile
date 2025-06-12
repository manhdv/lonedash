FROM python:3.11-slim

WORKDIR /code

# Copy và cài requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project
COPY . .

# Cho phép chạy script
RUN chmod +x entrypoint.sh

# Dùng entrypoint thay cho CMD trực tiếp
ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
