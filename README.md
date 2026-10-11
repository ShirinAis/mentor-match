# Mentor Match — Ментор-студент сәйкестендіру (Нұсқа 28)

Flask + Flask-SQLAlchemy + Flask-Login + Jinja2 + SQLite жобасы.
Студент ментор табады, өтінім жібереді; ментор өтінімді қабылдайды немесе қабылдамайды.

## Мүмкіндіктер

- Тіркелу / кіру / шығу (Flask-Login), құпиясөз хэштеледі, CSRF қорғанысы
- Рөлдер: `admin` және `user` (user — студент немесе ментор профилімен)
- Модельдер: `User`, `Mentor`, `Student`, `MentorRequest` (1–көп байланыстар)
- CRUD: ментор, студент, өтінім (қосу / көру / өңдеу / өшіру)
- Іздеу, бағыт бойынша сүзгі, сорттау, пагинация (менторлар, студенттер, өтінімдер)
- Өтінім статусы: `pending → accepted / rejected / cancelled`
- Ментордың бос орын лимиті (`max_students`), қайталанатын өтінімге тыйым
- Форма валидациясы (`app/forms.py`)
- Файл жүктеу: ментор суреті (png/jpg/webp), студент CV (PDF) — кеңейтім + файл
  сигнатурасы тексеріледі, атауы `uuid` арқылы қауіпсіз құрылады, көлемі ≤ 5 MB
- 404 / 500 (және 400, 403, 413) custom беттері
- REST API (JSON)

## Орнату және іске қосу

```bash
python -m venv venv
# Windows: venv\Scripts\activate     Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # SECRET_KEY мәнін өзгертіңіз
flask --app run init-db     # кестелерді құру (қолданба іске қосылғанда да автоматты құрылады)
flask --app run seed        # тест деректерін толтыру
flask --app run run         # немесе: python run.py
```

Сайт: http://127.0.0.1:5000

## Тест аккаунттар

| Рөл | Логин | Құпиясөз |
|---|---|---|
| Admin | `admin` | `Admin123!` |
| Ментор | `mentor1`, `mentor2`, `mentor3` | `Mentor123!` |
| Студент | `student1`, `student2` | `Student123!` |

## Құрылым

```
mentor_match/
├── run.py, config.py, requirements.txt, .env, .gitignore
└── app/
    ├── __init__.py        # create_app, CSRF, қате өңдеушілер, CLI
    ├── models.py          # дерекқор модельдері
    ├── forms.py           # валидация
    ├── services.py        # өтінім логикасы (веб + API ортақ)
    ├── utils.py           # admin_required, файл жүктеу
    ├── auth/  main/  mentor_requests/  api/   # blueprint-тер (routes.py)
    ├── templates/  static/
```

## API

Жазу сұраныстары `Content-Type: application/json` талап етеді. Алдымен кіріңіз (session cookie).

| Метод | URL | Сипаттама |
|---|---|---|
| POST | `/api/login` | `{"username","password"}` |
| GET | `/api/mentors?q=&direction=&page=` | Менторлар тізімі |
| GET | `/api/mentors/<id>` | Бір ментор |
| GET | `/api/requests?status=` | Өз өтінімдері (admin — барлығы) |
| POST | `/api/requests` | `{"mentor_id":1,"message":"..."}` (студент) |
| PUT | `/api/requests/<id>` | `{"status":"accepted"}` немесе `{"message":"..."}` |
| DELETE | `/api/requests/<id>` | Өтінімді өшіру |

```bash
curl -c cj -H "Content-Type: application/json" -d '{"username":"student1","password":"Student123!"}' localhost:5000/api/login
curl -b cj localhost:5000/api/requests
curl -b cj -H "Content-Type: application/json" -d '{"mentor_id":3,"message":"Сәлем, менторлыққа өтінім."}' localhost:5000/api/requests
```

## Демо сценарий

1. `student1` ретінде кіру → менторларды іздеу/сүзу → ментор бетінен өтінім жіберу.
2. Шығу → `mentor1` ретінде кіру → «Өтінімдер» → «Қабылдау».
3. `admin` ретінде кіру → менторды қосу/өңдеу/өшіру, студенттер тізімі, барлық өтінім.
4. Профильде сурет / CV жүктеу; жарамсыз файлды жүктеп тексеру.
5. Жоқ бетті ашу (`/xyz`) → custom 404.

## Скриншоттар

`screenshots/` папкасына 6–10 сурет қосыңыз: басты бет, іздеу/сүзгі, ментор беті,
тіркелу, өтінімдер тізімі, admin студенттер тізімі, профиль формасы, 404 беті.
