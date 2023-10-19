# Проект — Foodgram
## Онлайн-сервис «Продуктовый помощник»
### Описание
На этом сервисе вы можете опубликовать свой рецепт, посмортеть рецепты других пользователей, подписаться на автора рецептов и добавить понравившиеся рецепты в избранное. Также есть возможность добавить ингредиенты выбранных Вами рецептов в список покупок.
https://dlozk.ddns.net/
### Технологии
- Python 3.9
- Django - фреймворк для веб-приложений на языке Python.
- Django REST Framework
- PostgreSQL
- Gunicorn
- Docker

### Запуск проекта:
- Клонировать репозиторий
```
git@github.com:dlozko/foodgram-project-react.git
```
- Перейти в директорию foodgram-project-react.git
```
cd foodgram-project-react
```
### -При запуске проекта локально в контейнерах:
- Перейти в директорию infra
```
cd infra
```
- Запустить docker-compose:
```
docker-compose up
```
- После сборки контейнеров выполнить миграции:
```
docker-compose exec backend python manage.py migrate
```
- Создать суперпользователя:
```
docker-compose exec backend python createsuperuser
```
- Загрузить статику:
```
docker-compose exec backend python collectstatic --no-input
```
- Загрузить ингредиенты:
```
docker-compose exec backend python manage.py load_ingredients --path data/ingredients.csv
```
- Проверить работу foodgram по ссылке:
http://localhost/api/docs/

### -При запуске проекта локально:
### Backend
- Cоздать и активировать виртуальное окружение:
```
python -m venv venv
```
```
source venv/Scripts/activate
```
```
python -m pip install --upgrade pip
```
- Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
- Выполнить миграции:
```
python3 manage.py migrate
```
- Запустить проект:
```
python3 manage.py runserver
```
#### В API доступны следующие эндпоинты:
Доступно без токена:
* ```/api/users/```  Get-запрос – получение списка пользователей. POST-запрос – регистрация нового пользователя.

* ```/api/users/{id}``` GET-запрос – страница пользователя с указанным id.

* ```/api/tags/``` GET-запрос — получение списка тегов.

* ```/api/tags/{id}``` GET-запрос — получение информации о теге по его id.

* ```/api/ingredients/``` GET-запрос – получение списка ингредиентов.

* ```/api/ingredients/{id}/``` GET-запрос — получение информации об ингредиенте по id.

* ```/api/recipes/``` GET-запрос – получение списка всех рецептов.

* ```/api/recipes/{id}/``` GET-запрос – получение информации о рецепте по id.

* ```/api/users/me/``` GET-запрос – страница текущего пользователя. PATCH-запрос – редактирование своей страницы.

* ```/api/users/set_password``` POST-запрос – изменение пароля.

* ```/api/recipes/``` POST-запрос – добавление нового рецепта.

* ```/api/recipes/?is_favorited=1``` GET-запрос – получение списка рецептов, добавленных в избранное. 

* ```/api/recipes/is_in_shopping_cart=1``` GET-запрос – получение списка рецептов, добавленных в покупки.

* ```/api/recipes/{id}/``` PATCH-запрос – изменение собственного рецепта (доступно для автора рецепта). DELETE-запрос – удаление собственного рецепта.

* ```/api/recipes/{id}/favorite/``` POST-запрос – добавление рецепта в избранное. DELETE-запрос – удаление рецепта из избранного.

* ```/api/recipes/{id}/shopping_cart/``` POST-запрос – добавление нового рецепта в покупки. DELETE-запрос – удаление рецепта из покупок.

* ```/api/recipes/download_shopping_cart/``` GET-запрос – получение txt. файла со списком покупок.

* ```/api/users/{id}/subscribe/``` GET-запрос – подписка на пользователя по id. POST-запрос – отписка от пользователя по id.

* ```/api/users/subscriptions/``` GET-запрос – получение списка пользователей, на которых подписан пользователь.

### При запуске проекта на сервере:
- Установить на сервере docker и docker-compose. Скопировать на сервер файлы docker-compose.yaml и default.conf:
- Cоздать и заполнить .env файл в директории infra
```
SECRET_KEY = секретный ключ
POSTGRES_DB=postgres
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
DB_NAME=foodgram
DEBUG=True
ALLOWED_HOSTS=*
```
- После успешного запуска контрейнеров боевом сервере должны будут выполнены следующие команды:
```
sudo docker-compose exec backend python manage.py migrate
```
```
sudo docker-compose exec backend python manage.py collectstatic
```
Затем необходимо будет создать суперюзера и загрузить в базу данных информацию об ингредиентах:
```
sudo docker-compose exec backend python manage.py createsuperuser
```
```
sudo docker-compose exec backend python manage.py load_ingredients --path data/ingredients.csv
```
### Проект доступен по ссылке:
```
https://dlozk.ddns.net/

Проект доступен по ссылке:
```
### Автор
- Денис Лозко
```
https://github.com/dlozko
```