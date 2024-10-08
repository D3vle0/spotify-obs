FROM python:3.9.6
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8888
CMD ["flask", "run", "--host=0.0.0.0", "--port=8888"]
