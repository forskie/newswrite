
# 📰 NewsWrite

> Современное веб-приложение для создания и публикации статей с полноценной системой взаимодействия

## 📋 Описание

NewsWrite — это интуитивное веб-приложение для написания и публикации статей. Проект демонстрирует полноценный стек технологий для создания современного блог-платформы с системой авторизации, комментариев и социальных взаимодействий.

Основные возможности

- 🔐 **Полная система аутентификации**
  - Регистрация пользователей через email
  - Безопасная авторизация с хешированием паролей
  - Управление сессиями

- 📝 **Управление статьями**
  - Создание, редактирование и удаление статей
  - Rich-text редактор для форматирования
  - Загрузка и управление изображениями
  - Предпросмотр статей перед публикацией

- 💬 **Социальное взаимодействие**
  - Система комментариев под статьями
  - Лайки и реакции на публикации
  - Профили пользователей

- 🖼️ **Работа с медиа**
  - Загрузка изображений к статьям
  - Автоматическая оптимизация размера
  - Безопасное хранение файлов

## 🛠️ Технологический стек

### Backend
- **Python 3.12.10** — основной язык программирования
- **Flask 3.0** — веб-фреймворк
- **Flask-SQLAlchemy** — ORM для работы с базой данных
- **Flask-Login** — управление сессиями пользователей
- **Flask-WTF** — формы и CSRF защита
- **Flask-Migrate** — миграции базы данных

### База данных
- **SQLite** (для разработки) / **PostgreSQL** (для продакшена)

### Frontend
- **Jinja2** — шаблонизатор
- **Bootstrap 5** — CSS фреймворк
- **JavaScript** — интерактивность

### Безопасность
- **Werkzeug Security** — хеширование паролей
- **Flask-WTF** — защита от CSRF атак
- Валидация пользовательского ввода
- Безопасная загрузка файлов

## 🚀 Быстрый старт

### Требования

- Python 3.9 или выше
- pip (менеджер пакетов Python)
- virtualenv (рекомендуется)

### Установка

1. **Клонируйте репозиторий**
```bash
git clone https://github.com/forskie/newswrite.git
cd newswrite
```

2. **Создайте виртуальное окружение**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Установите зависимости**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения**
```bash
# Создайте файл .env в корне проекта
cp .env.example .env

# Отредактируйте .env и укажите свои значения
```

Пример `.env`:
```env
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///newswrite.db
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=16777216
```

5. **Инициализируйте базу данных**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. **Запустите приложение**
```bash
flask run
```

Приложение будет доступно по адресу: `http://localhost:5000`

## 📁 Структура проекта

```
newswrite/
│
├── app/
│   ├── __init__.py           # Инициализация Flask приложения
│   ├── models.py             # Модели базы данных
│   ├── forms.py              # Формы WTForms
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py           # Роуты авторизации
│   │   ├── articles.py       # Роуты для статей
│   │   └── comments.py       # Роуты комментариев
│   ├── templates/            # HTML шаблоны
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── auth/
│   │   └── articles/
│   └── static/               # Статические файлы
│       ├── css/
│       ├── js/
│       └── uploads/          # Загруженные файлы
│
├── migrations/               # Миграции базы данных
├── tests/                    # Тесты
│   ├── test_auth.py
│   ├── test_articles.py
│   └── test_comments.py
│
├── .env.example              # Пример переменных окружения
├── .gitignore               # Git ignore файл
├── config.py                # Конфигурация приложения
├── requirements.txt         # Python зависимости
├── run.py                   # Точка входа
└── README.md                # Документация
```

## 🔑 Основные модели данных

### User (Пользователь)
```python
- id: Integer (Primary Key)
- username: String (Unique)
- email: String (Unique)
- password_hash: String
- created_at: DateTime
- articles: Relationship
- comments: Relationship
- likes: Relationship
```

### Article (Статья)
```python
- id: Integer (Primary Key)
- title: String
- content: Text
- image_url: String
- author_id: Foreign Key (User)
- created_at: DateTime
- updated_at: DateTime
- comments: Relationship
- likes: Relationship
```

### Comment (Комментарий)
```python
- id: Integer (Primary Key)
- content: Text
- user_id: Foreign Key (User)
- article_id: Foreign Key (Article)
- created_at: DateTime
```

### Like (Лайк)
```python
- id: Integer (Primary Key)
- user_id: Foreign Key (User)
- article_id: Foreign Key (Article)
- created_at: DateTime
```

## 🧪 Тестирование

Запуск тестов:
```bash
# Все тесты
pytest

# С покрытием кода
pytest --cov=app tests/

# Конкретный файл
pytest tests/test_auth.py
```

## 🐳 Docker

Запуск с помощью Docker:

```bash
# Сборка образа
docker build -t newswrite .

# Запуск контейнера
docker run -p 5000:5000 newswrite
```

Или используйте Docker Compose:
```bash
docker-compose up
```

## 📚 API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/` | Главная страница со списком статей |
| GET/POST | `/register` | Регистрация нового пользователя |
| GET/POST | `/login` | Вход в систему |
| GET | `/logout` | Выход из системы |
| GET | `/articles` | Список всех статей |
| GET | `/articles/<id>` | Просмотр конкретной статьи |
| GET/POST | `/articles/create` | Создание новой статьи |
| GET/POST | `/articles/<id>/edit` | Редактирование статьи |
| POST | `/articles/<id>/delete` | Удаление статьи |
| POST | `/articles/<id>/like` | Лайк статьи |
| POST | `/articles/<id>/comment` | Добавление комментария |

## 🔒 Безопасность

Проект использует следующие меры безопасности:

- ✅ Хеширование паролей с использованием Werkzeug
- ✅ CSRF защита для всех форм
- ✅ Валидация и санитизация пользовательского ввода
- ✅ Защита от SQL-инъекций через ORM
- ✅ Ограничение размера загружаемых файлов
- ✅ Проверка типов загружаемых файлов
- ✅ Безопасное хранение конфиденциальных данных (.env)

## 🎯 Roadmap

- [ ] REST API для мобильных приложений
- [ ] Система тегов и категорий
- [ ] Полнотекстовый поиск
- [ ] Email уведомления
- [ ] Markdown редактор
- [ ] Пагинация статей
- [ ] Система рейтингов авторов
- [ ] Экспорт статей в PDF
- [ ] Интеграция с социальными сетями
- [ ] Админ-панель

## 🤝 Вклад в проект

Буду рад любому вкладу! Если вы хотите внести изменения:

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/AmazingFeature`)
3. Закоммитьте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Запушьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

## 👤 Автор

**forskie**

- GitHub: [@forskie](https://github.com/forskie)
- Email: forskiee@yahoo.com

## 🙏 Благодарности

- Flask документация и сообщество
- Bootstrap за отличный UI фреймворк
- Все контрибьюторы проекта

---

⭐ Если проект был полезен, поставьте звезду на GitHub!
