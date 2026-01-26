FROM python:3.9-slim
RUN pip install streamlit requests pandas
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]