Проект [Foodgram](https://f00d9r4m.run.place/) позволяет пользователям
создавать кулинарные рецепты, скачивать списки продуктов, необходимых для
приготовления блюд, подписываться на других пользователей и сохранять
рецепты в избранное.

#### Технологии изпользовавшиеся в разработке проекта:

- Django
- DRF
- Djoser
- PostgreSQL
- Nginx
- Gunicorn
- Docker

#### Документация API с примерами запросов: https://f00d9r4m.run.place/api/docs/

### Запуск проекта

#### 1. Клонирование репозитория

```bash
git clone https://github.com/your-repo/foodgram.git
cd foodgram
```

#### 2. Настройка переменных окружения

Создайте файл `.env` в корневой директории и укажите настройки:

(`SECRET_KEY` можно сгенерировать командой:

```bash
python -c
'from django.core.management.utils import get_random_secret_key; \
print(get_random_secret_key())'
```
)

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=сгенерированный SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1  # Для сервера укажите домен или IP
```

#### 3. Запуск контейнеров

```bash
docker-compose up -d --build
```

#### 4. Загрузка ингредиентов и тегов в базу

```bash
docker-compose exec backend python manage.py load_tags tags.json
```
```bash
docker-compose exec backend python manage.py load_ingredients ingredients.json
```

Автор проекта: [Иван Подгорный](https://github.com/yvespracticum)
