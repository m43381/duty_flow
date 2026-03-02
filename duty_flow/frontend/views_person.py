from core.crud import crud_views
from people.models import Person
from people.forms import PersonForm

# Создаем CRUD для сотрудников одной строкой!
person_views = crud_views(
    model=Person,
    form_class=PersonForm,
    template_prefix='person',
    extra_context={'some_extra': 'data'}
)

# Экспортируем view-функции
person_list = person_views['list']
person_add = person_views['create']
person_edit = person_views['update']
person_delete = person_views['delete']
person_detail = person_views['detail']