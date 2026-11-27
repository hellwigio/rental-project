# Rental Project

Backend для аренды жилья в Германии. Django REST Framework, MySQL и Docker Compose.

## Схема данных

| Django-приложение | Таблица | Данные |
| --- | --- | --- |
| `apps/users` | `users_user` | Уникальный email для входа, имя, хеш пароля и служебные поля Django Auth. |
| `apps/listings` | `listings_listing` | Владелец, заголовок, описание, город, район, тип жилья, количество комнат, цена за ночь в EUR, признак видимости и даты создания и изменения. |
| `apps/bookings` | `bookings_booking` | Объявление, арендатор, даты заезда и выезда, статус и даты создания и изменения. |
| `apps/reviews` | `reviews_review` | Бронирование, оценка 1–5, комментарий и дата создания. Автор и объявление определяются через бронь. |

У пользователя может быть несколько объявлений и бронирований. У объявления
может быть несколько бронирований, а у бронирования — не больше одного отзыва.
Группы `renter` и `landlord` хранятся в `auth_group`, а членство — в
`users_user_groups`. Начальная миграция создаёт обе группы. Пользователь может
состоять в обеих группах. При создании через `create_user()` он получает группу
`renter`.
Даты хранятся как календарные дни. Дата выезда исключается из интервала
`[start_date, end_date)`, поэтому выезд и следующий заезд могут быть в один день.
Схема проверяет порядок дат, положительную цену, количество комнат и диапазон
оценок. Индексы покрывают сортировку активных объявлений по цене и дате создания,
поиск броней объявления по датам и выборку броней арендатора по дате выезда.

История бронирований и отзывов защищена внешними ключами. Объявление без броней
можно удалить. Для объявления с историей предусмотрено скрытие через `is_active`.

## Компоненты

1. Поднять отдельные сервисы `db` и `django` через Docker Compose. Данные MySQL
   сохраняются в томе `mysql_data`. Порт базы доступен внутри сети Compose.
2. Создать пользовательскую модель до первой миграции, затем описать
   объявления, бронирования и отзывы. Модели лежат в пакете `models/` каждого
   приложения. Маршруты приложений подключаются через `apps/urls.py`.
3. Применить миграции к чистой базе и проверить связность и ограничения схемы.

## Запуск

Скопируйте шаблон командой `cp .env.example .env` и заполните в `.env`
`DJANGO_SECRET_KEY`, `MYSQL_PASSWORD` и `MYSQL_ROOT_PASSWORD` локальными значениями.
Затем запустите из корня проекта:

```sh
docker compose up --build -d
docker compose logs -f django
```

Django ждёт готовности MySQL, применяет миграции и запускает Gunicorn
на `127.0.0.1:8000`. Проверить окружение и применённые миграции:

```sh
docker compose exec django python manage.py check --database default
docker compose exec django python manage.py showmigrations
docker compose exec django python manage.py makemigrations --check --dry-run
```

После изменения кода пересоберите образ командой `docker compose up --build -d`.
При запуске Django напрямую для локальной разработки можно указать
`DJANGO_USE_SQLITE=true`. Docker Compose использует MySQL.

## HTTP API

Базовый путь `/api/`. Тела запросов — JSON. Списки используют страницы
`page` и `page_size` (по умолчанию 20, максимум 100).
Для входа запросите `GET /api/users/csrf/`, сохраните cookie и передайте
`csrfToken` в заголовке `X-CSRFToken` при логине. После логина используйте
обновлённый токен из ответа и cookie сессии для изменяющих запросов.

| Маршрут после /api/ | Действие |
| --- | --- |
| POST users/register/ | Имя, email и пароль в полях name, email, password |
| POST users/login/, users/logout/ | Вход по email/password и завершение сессии |
| POST users/landlord/ | Самостоятельно подключить возможность сдавать жильё |
| GET, POST listings/ | Публичный каталог и создание объявления арендодателем |
| GET, PUT, PATCH, DELETE listings/{id}/ | Просмотр, редактирование или удаление. Для скрытия PATCH с is_active=false |
| GET listings/mine/ | Все свои объявления, включая скрытые |
| GET listings/popular/ | 20 наиболее частых поисковых запросов |
| GET, POST bookings/ | Свои брони и заявки на свои объекты. При создании передать listing, start_date, end_date |
| GET bookings/{id}/ | Одна бронь для участника |
| PATCH bookings/{id}/status/ | Поле status. Владелец принимает или отклоняет pending, отмечает заезд confirmed во время проживания. Арендатор отменяет pending или confirmed не позднее чем за два дня до заезда |
| GET, POST reviews/ | Отзывы. Фильтр booking__listing по ID объявления. Для создания передать booking, rating и comment |

Пример поиска: `GET /api/listings/?city=Berlin&min_rooms=2&max_price=120&search=park&ordering=nightly_price`.
Поддерживаются также district, housing_type, min_price, max_rooms. Сортировка по
nightly_price, created_at, views и reviews, префикс минус задаёт убывание.
Детальный просмотр публичного объявления записывает событие просмотра.
Фильтр `period=active` или `period=completed` ограничивает список бронирований.

## Проверка и защита

GitHub Actions запускает Compose с пустой MySQL, проверяет миграции, полный
HTTP-сценарий, одновременное бронирование и сохранность данных после перезапуска.
Локально для тестов нужен доступ пользователя БД к отдельной базе test_rental.
Затем выполните `docker compose exec django python manage.py test`.

На защите покажите создание двух аккаунтов, подключение группы landlord, создание
объявления, поиск, бронь и её подтверждение. Объясните, как блокировка строки
объявления предотвращает пересечения и почему отзыв привязан к проживанию.
Тест tests/test_rental.py демонстрирует проверку дат заселения и выезда.

## Развёртывание на EC2

На Linux-хосте с Docker и Compose клонируйте проект, настройте .env, укажите
публичное доменное имя в DJANGO_ALLOWED_HOSTS, DJANGO_DEBUG=false и DJANGO_HTTPS=true.
Запустите `docker compose up --build -d`. Порт Gunicorn привязан к loopback.
Настройте HTTPS reverse proxy на хосте до 127.0.0.1:8000, сохраняя заголовок Host
и перезаписывая X-Forwarded-Proto. Например, для Caddy достаточно блока:

```caddy
rentals.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Подставьте свой домен и направьте DNS на EC2. Разрешите входящие 80/443 для
HTTPS, SSH ограничьте своим адресом. Проверьте GET /api/listings/ через HTTPS.

### Новый сервер в Стокгольме через Terraform

Конфигурация в `infra/` создаёт один EC2 t3.small, зашифрованный корневой диск
20 GiB gp3, Elastic IP и security group. Нужны AWS-доступ, публичная подсеть
в eu-north-1, существующая пара ключей EC2 и IPv4 администратора для SSH.
Задайте subnet_id, key_name, admin_ipv4 в infra/terraform.tfvars.
Выполните в infra:

```sh
terraform init
terraform plan -out=rental.tfplan
terraform apply rental.tfplan
terraform output -raw catalog_url
```

Имя nip.io формируется из выделенного Elastic IP автоматически. Cloud-init установит Docker,
Compose и Caddy, сгенерирует секреты на сервере и поднимет проверенную версию
приложения. После завершения cloud-init проверьте HTTPS по catalog_url.
Для диагностики подключитесь как ubuntu и выполните `cloud-init status --long`
и `sudo journalctl -u rental -u caddy`. Данные MySQL размещаются на корневом
EBS-диске. Terraform блокирует уничтожение EC2 через prevent_destroy.
Для обновления приложения на месте выберите новый проверенный коммит в
/opt/rental-project и выполните `sudo systemctl restart rental`.
