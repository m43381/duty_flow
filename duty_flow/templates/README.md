
### ПОЯСНИТЕЛЬНАЯ ЗАПИСКА ДЛЯ ПАПКИ TEMPLATES

Создайте файл `templates/README.md`:

```markdown
# Структура шаблонов в проекте DutyFlow

## Общая структура
templates/
├── base.html # Базовый шаблон (скелет страницы)
├── index.html # Главная страница
├── registration/ # Шаблоны аутентификации
│ └── login.html # Страница входа
├── cabinets/ # Личные кабинеты
│ ├── base_cabinet.html # Базовый шаблон кабинета
│ ├── dashboard.html # Дашборд (главная после входа)
│ ├── person_list.html # Список сотрудников
│ ├── plan_list.html # Список планов нарядов
│ ├── type_list.html # Список типов нарядов
│ ├── unit_list.html # Список подразделений
│ ├── user_list.html # Список пользователей
│ ├── access_denied.html # Страница отказа в доступе
│ └── *.html # Другие страницы кабинетов
├── components/ # Переиспользуемые компоненты
│ └── navigation.html # Навигационное меню
└── admin/ # Кастомная админка (если будет)



## 1. Базовые шаблоны

### `base.html`
Главный скелет всех страниц. Содержит:
- Подключение CSS и JS
- Кнопку переключения темы
- Блоки для контента (`{% block content %}`)

```html
{% block title %}...{% endblock %}    - Заголовок страницы
{% block content %}...{% endblock %}  - Основной контент
{% block extra_css %}...{% endblock %} - Дополнительные CSS
{% block extra_js %}...{% endblock %}  - Дополнительные JS

cabinets/base_cabinet.html
Базовый шаблон для всех страниц личного кабинета. Содержит:

Шапку с информацией о пользователе

Навигационное меню (подключает components/navigation.html)

Блок {% block cabinet_content %} для контента

2. Компоненты
components/navigation.html
Навигационное меню с учетом прав доступа:

Дашборд (все)

Сотрудники (все)

Планы нарядов (все)

Типы нарядов (академия и факультет)

Подразделения (только академия)

Пользователи (только академия)

Активный пункт меню подсвечивается через active_tab.

3. Страницы кабинетов
cabinets/dashboard.html
Главная страница после входа:

Статистика (карточки сверху)

Ближайшие наряды

Информация о подразделении

cabinets/person_list.html
Список сотрудников (в разработке)

cabinets/plan_list.html
Список планов нарядов (в разработке)

cabinets/access_denied.html
Страница, показываемая при попытке доступа к запрещенному разделу.

4. Шаблоны аутентификации
registration/login.html
Страница входа:

Форма с полями "Логин" и "Пароль"

Обработка ошибок

Ссылка на главную

Переменные, доступные в шаблонах
От views:
Переменная	Описание
page_title	Заголовок страницы
active_tab	Активный пункт меню (dashboard, people, plans...)
От контекстного процессора (будет добавлен позже):
Переменная	Описание
user.profile.unit	Подразделение пользователя
user.profile.access_level	Уровень доступа
user.profile.get_access_level_display	Русское название уровня
Добавление новой страницы
Создайте шаблон в соответствующей папке:

Для кабинета: cabinets/имя_страницы.html

Для компонента: components/имя_компонента.html

Если это страница кабинета, расширьте base_cabinet.html:

{% extends 'cabinets/base_cabinet.html' %}

{% block cabinet_content %}
  <!-- ваш контент -->
{% endblock %}
3. Добавьте view и url

Пример использования переменных
{% if user.profile.access_level == 'academy' %}
  <p>Вы видите это, потому что вы академия</p>
{% endif %}

<p>Ваше подразделение: {{ user.profile.unit.name }}</p>
<p>Ваша роль: {{ user.profile.get_access_level_display }}</p>

Наследование шаблонов
base.html
├── registration/login.html
└── cabinets/base_cabinet.html
    ├── cabinets/dashboard.html
    ├── cabinets/person_list.html
    ├── cabinets/plan_list.html
    └── ...


Блоки в шаблонах
В base.html:
title - заголовок страницы

content - основной контент

extra_css - доп. CSS

extra_js - доп. JavaScript

В cabinets/base_cabinet.html:
все блоки из base.html

cabinet_content - контент кабинета

Советы по шаблонам
Не дублируйте код - выносите повторяющиеся части в components/

Проверяйте права доступа - используйте {% if user.profile.access_level == '...' %}

Используйте include для компонентов - {% include 'components/navigation.html' %}

Давайте осмысленные имена файлам и блокам

Пример создания нового компонента
Шаг 1. Создайте файл components/my_component.html:

<div class="my-component">
  <h3>{{ title }}</h3>
  <p>{{ content }}</p>
</div>

Шаг 2. Используйте в любом шаблоне:
{% include 'components/my_component.html' with title='Заголовок' content='Текст' %}


Полезные теги Django
Тег	Описание
{% url 'name' %}	Генерация URL по имени
{% if ... %}	Условный оператор
{% for ... in ... %}	Цикл
{% include %}	Включение другого шаблона
{% block %}	Определение блока
{% extends %}	Наследование шаблона
{% csrf_token %}	CSRF-токен для форм
