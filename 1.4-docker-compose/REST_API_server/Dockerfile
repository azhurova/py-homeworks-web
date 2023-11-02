FROM python:3.10-alpine
# RUN apk add --no-cache bash
# RUN apk add --no-cache curl

WORKDIR /usr/src/

COPY ./stocks_products/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

COPY ./stocks_products/entrypoint.sh ./entrypoint.sh
RUN sed -i 's/\r$//g' entrypoint.sh
RUN chmod +x entrypoint.sh

COPY ./stocks_products .

EXPOSE 8000

ENTRYPOINT ["/usr/src/entrypoint.sh"]
