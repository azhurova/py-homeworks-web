FROM python:3.10-alpine
# RUN apk add --no-cache bash
# RUN apk add --no-cache curl

WORKDIR src
COPY ./stocks_products/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

COPY ./stocks_products .
RUN python3 manage.py migrate

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]