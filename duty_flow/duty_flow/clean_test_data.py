"""
Скрипт для очистки тестовых данных в системе DutyFlow.
Удаляет все тестовые данные, оставляя только необходимые для работы системы.
Запуск: python manage.py shell < scripts/clean_test_data.py
Или скопировать и вставить в shell
"""

import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'duty_flow.settings')
django.setup()

from django.contrib.auth.models import User
from units.models import Unit, UnitType
from ranks.models import Rank
from people.models import Person, Exemption, DutyType, DutyClearance
from duty_plans.models import DutyPlan, DutyAssignment
from users_app.models import UserProfile

print("=" * 60)
print("🧹 НАЧАЛО ОЧИСТКИ ТЕСТОВЫХ ДАННЫХ")
print("=" * 60)

# Счетчики удаленных записей
stats = {}

# 1. Удаляем назначения на наряды (DutyAssignment)
print("\n📋 1. Удаление назначений на наряды...")
count = DutyAssignment.objects.all().count()
DutyAssignment.objects.all().delete()
stats['Назначения'] = count
print(f"  ✅ Удалено: {count}")

# 2. Удаляем планы нарядов (DutyPlan)
print("\n📅 2. Удаление планов нарядов...")
count = DutyPlan.objects.all().count()
DutyPlan.objects.all().delete()
stats['Планы нарядов'] = count
print(f"  ✅ Удалено: {count}")

# 3. Удаляем допуски к нарядам (DutyClearance)
print("\n🔓 3. Удаление допусков к нарядам...")
count = DutyClearance.objects.all().count()
DutyClearance.objects.all().delete()
stats['Допуски'] = count
print(f"  ✅ Удалено: {count}")

# 4. Удаляем освобождения (Exemption)
print("\n🔓 4. Удаление освобождений...")
count = Exemption.objects.all().count()
Exemption.objects.all().delete()
stats['Освобождения'] = count
print(f"  ✅ Удалено: {count}")

# 5. Удаляем сотрудников (Person), но оставляем нескольких для теста (опционально)
print("\n👥 5. Удаление сотрудников...")

# Вариант А: Удалить всех сотрудников
count = Person.objects.all().count()
Person.objects.all().delete()
stats['Сотрудники'] = count
print(f"  ✅ Удалено: {count}")

# Раскомментируйте Вариант Б, если хотите оставить несколько сотрудников
"""
# Вариант Б: Оставить только 5 сотрудников для минимального тестирования
total = Person.objects.all().count()
if total > 5:
    # Оставляем первых 5 (самых старых)
    to_keep = Person.objects.all()[:5]
    to_delete = Person.objects.exclude(id__in=[p.id for p in to_keep])
    count = to_delete.count()
    to_delete.delete()
    print(f"  ✅ Удалено: {count} (оставлено 5)")
else:
    print(f"  ⚠️ Сотрудников и так мало: {total}")
stats['Сотрудники'] = count
"""

# 6. Удаляем тестовых пользователей (кроме admin)
print("\n👤 6. Удаление тестовых пользователей...")

# Список тестовых пользователей для удаления
test_usernames = ['academy', 'faculty', 'faculty2', 'dept', 'dept2', 'commandant', 'staff', 'test_user']
deleted_count = 0

for username in test_usernames:
    try:
        user = User.objects.get(username=username)
        # Не удаляем суперпользователей
        if not user.is_superuser:
            user.delete()
            deleted_count += 1
            print(f"  ✅ Удален: {username}")
        else:
            print(f"  ⚠️ Пропущен (суперпользователь): {username}")
    except User.DoesNotExist:
        print(f"  ⚠️ Не найден: {username}")

stats['Тестовые пользователи'] = deleted_count

# 7. Удаляем созданные типы нарядов (DutyType), но оставляем базовые
print("\n📌 7. Удаление тестовых типов нарядов...")

# Вариант А: Удалить все типы нарядов
count = DutyType.objects.all().count()
DutyType.objects.all().delete()
stats['Типы нарядов'] = count
print(f"  ✅ Удалено: {count}")

# Раскомментируйте Вариант Б, если хотите оставить базовые типы
"""
# Вариант Б: Оставить только 3 базовых типа
basic_types = ['Дежурный по КПП', 'Дежурный по парку', 'Дежурный по штабу']
to_delete = DutyType.objects.exclude(name__in=basic_types)
count = to_delete.count()
to_delete.delete()
print(f"  ✅ Удалено тестовых типов: {count}")
stats['Типы нарядов'] = count
"""

# 8. Удаляем тестовые подразделения (Unit), кроме основных
print("\n🏛️ 8. Очистка подразделений...")

# Созданные подразделения не удаляем, так как они нужны для работы
# Но можно удалить дубликаты, если они есть
print("  ⚠️ Подразделения сохранены (необходимы для работы)")

# 9. Проверяем и очищаем профили без пользователей
print("\n🔄 9. Очистка профилей без пользователей...")
orphaned_profiles = UserProfile.objects.filter(user__isnull=True)
count = orphaned_profiles.count()
orphaned_profiles.delete()
stats['Профили-сироты'] = count
print(f"  ✅ Удалено профилей без пользователей: {count}")

# 10. ИТОГИ
print("\n" + "=" * 60)
print("✅ ОЧИСТКА ТЕСТОВЫХ ДАННЫХ ЗАВЕРШЕНА!")
print("=" * 60)

print(f"\n📊 Статистика удалений:")
total_deleted = 0
for key, value in stats.items():
    if value > 0:
        print(f"  • {key}: {value}")
        total_deleted += value

print(f"\n📦 ВСЕГО УДАЛЕНО: {total_deleted} записей")

print("\n🏛️ Оставшиеся данные:")
print(f"  • Типы подразделений: {UnitType.objects.count()}")
print(f"  • Подразделения: {Unit.objects.count()}")
print(f"  • Звания: {Rank.objects.count()}")
print(f"  • Пользователи (без тестовых): {User.objects.exclude(username__in=test_usernames).count()}")

print("\n👑 Сохраненные пользователи:")
for user in User.objects.filter(is_superuser=True):
    print(f"  • {user.username} (суперпользователь)")

print("\n💡 Чтобы создать новые тестовые данные, запустите:")
print("   python manage.py shell < scripts/create_test_data.py")
print("\n" + "=" * 60)