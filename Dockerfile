FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ /app/src/
COPY tests /app/tests/
EXPOSE 8000
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
