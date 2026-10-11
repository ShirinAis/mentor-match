from .extensions import db
from .models import Mentor, MentorRequest, Student, User


def _user(username, email, password, role="user"):
    u = User(username=username, email=email, role=role)
    u.set_password(password)
    db.session.add(u)
    db.session.flush()
    return u


def seed_data():
    if User.query.filter_by(username="admin").first():
        print("Тест деректері бұрын қосылған.")
        return

    _user("admin", "admin@example.com", "Admin123!", role="admin")

    m_users = [
        ("mentor1", "Айдар Сейтқали", "Веб-әзірлеу", "Python, Flask, SQL", 6),
        ("mentor2", "Дана Нұрланқызы", "Жасанды интеллект", "ML, NLP, Python", 4),
        ("mentor3", "Ерлан Бекұлы", "Киберқауіпсіздік", "Pentest, Linux, Network", 8),
    ]
    mentors = []
    for username, name, direction, topics, exp in m_users:
        u = _user(username, f"{username}@example.com", "Mentor123!")
        m = Mentor(user_id=u.id, full_name=name, direction=direction, topics=topics,
                   bio=f"{name} — {direction} саласындағы тәжірибелі маман.",
                   experience_years=exp, max_students=3)
        db.session.add(m)
        mentors.append(m)

    extra = [
        ("Мадина Қасымова", "UI/UX дизайн", "Figma, Research", 5),
        ("Тимур Алиев", "Деректер ғылымы", "Pandas, SQL, BI", 7),
        ("Салтанат Жұмабай", "Мобильді әзірлеу", "Flutter, Android", 3),
        ("Нұрсұлтан Омаров", "Қаржы және бизнес", "Стартап, Финанс", 10),
        ("Әсел Темірхан", "Карьера және резюме", "Резюме, Интервью", 9),
    ]
    for name, direction, topics, exp in extra:
        db.session.add(Mentor(full_name=name, direction=direction, topics=topics,
                              bio=f"{name} — {direction} бағыты бойынша ментор.",
                              experience_years=exp, max_students=2))

    students = []
    for i, (username, name, interest) in enumerate(
            [("student1", "Алия Ермекова", "Веб-әзірлеу"),
             ("student2", "Данияр Мақсат", "Жасанды интеллект")], start=1):
        u = _user(username, f"{username}@example.com", "Student123!")
        s = Student(user_id=u.id, full_name=name, interest=interest, course=i + 1,
                    goal="Жақсы жұмыс табу және тәжірибе жинау.", phone="+77011234567")
        db.session.add(s)
        students.append(s)

    db.session.flush()
    db.session.add(MentorRequest(mentor_id=mentors[0].id, student_id=students[0].id,
                                 message="Сәлеметсіз бе! Flask бойынша маған көмектесіңізші.",
                                 status="pending"))
    db.session.add(MentorRequest(mentor_id=mentors[1].id, student_id=students[1].id,
                                 message="ML саласына кіру үшін бағыт көрсетіңіз.",
                                 status="accepted"))
    db.session.commit()
