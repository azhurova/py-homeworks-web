FROM python:3.10-alpine
# RUN apk add --no-cache bash
# RUN apk add --no-cache curl

WORKDIR /usr/src/

COPY ./requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

COPY ./ ./

EXPOSE 8080

CMD ["python3", "server.py"]
