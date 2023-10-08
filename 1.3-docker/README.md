# Домашнее задание к лекции «Docker»

Инструкцию по сдаче домашнего задания вы найдете на главной странице репозитория. 

## Задание 1

### Каталог `my_nginx`

Сборка docker image
```bash
docker image build . --tag=my_nginx
```
Создание docker container
```bash
docker container create -p 5000:80 --name=my_nginx_container my_nginx
```

Запуск docker container
```bash
docker container start my_nginx_container
```

Быстрый запуск docker container
```bash
docker run -d -p 5000:80 my_nginx
```

## Задание 2

### Каталог `REST_API_server`

Сборка docker image
```bash
docker image build . --tag=rest_api_server
```
Создание docker container
```bash
docker container create -p 8000:8000 --name=rest_api_server_container rest_api_server
```

Запуск docker container
```bash
docker container start rest_api_server_container
```

Быстрый запуск docker container
```bash
docker run -d -p 8000:8000 rest_api_server
```

примеры API-запросов в файле
[rest_api_server_requests_examples.http](rest_api_server_requests_examples.http)