FROM python:3.9-slim

WORKDIR /root

COPY . .

RUN chmod 777 *.sh && pip install -r requirements.txt

EXPOSE 8000
EXPOSE 5557

CMD ["sh", "master.sh"]