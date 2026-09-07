[![Workflow for foodgram](https://github.com/a-roslyakov/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/a-roslyakov/foodgram/actions/workflows/main.yml)

### Foodgram
_API для web-приложения обмена рецептами. Позволяет пользователям делиться рецептами разных блюд. Есть возможность добавлять рецепты в избранное, подписываться на пользователей, добавлять рецепты в список покупок с дальнейшим скачиванием файла со списком нужных ингредиентов._

### Технологии

- _Python 3.12_
- _Django_
- _Django REST Framework_
- _Djoser_

### Запуск проекта
_Клонировать репозиаторий:_
```
git@github.com:a-roslyakov/foodgram.git
cd foodgram
```

_Создать и активировать виртуальное окружение:_

```
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

_Создайте и настройте файл окружения (см. раздел «Настройка окружения»)_

_Соберите и запустите контейнеры:_

```
docker compose up -d
```

_Выполните миграции в контейнере и перенесите их в нужную директорию:_

```
docker compose exec backend python manage.py migrate
docker compose exec backend cp -r /app/collected_static/. /backend_static/static
```

### Проект будет доступен по адресу `http://localhost:8000`


### Настройка окружения

```
Откройте файл `.env` и заполните следующие переменные:
   * `SECRET_KEY` — секретный ключ Django;
   * `DEBUG` — режим отладки (`True`/`False`);
   * `DB_NAME` — имя базы данных;
   * `DB_USER` — пользователь базы данных;
   * `DB_PASSWORD` — пароль пользователя базы данных;
   * `DB_HOST` — хост базы данных;
   * `DB_PORT` — порт базы данных.
```

### Примеры эндпоинтов

- `GET /api/recipes/` - список рецептов

```
{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=4",
  "previous": "http://foodgram.example.org/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Иванов",
        "is_subscribed": false,
        "avatar": "http://foodgram.example.org/media/users/image.png"
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.png",
      "text": "string",
      "cooking_time": 1
    }
  ]
}
```

- `POST /api/recipes/` - создать рецепт

```
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}
```

- `GET /api/recipes/download_shopping_cart/` - скачать список покупок

- `GET /api/tags/` - список тегов

```
[
  {
    "id": 0,
    "name": "Завтрак",
    "slug": "breakfast"
  }
]
```


### Автор
_Артём Росляков_
https://github.com/a-roslyakov