FROM python:3.8

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 3111

RUN "python3" "init_db.py"

CMD [ "python3", "app.py" ]