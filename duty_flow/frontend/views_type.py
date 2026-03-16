from core.crud import crud_views
from duty_types.models import DutyType
from duty_types.forms import DutyTypeForm

# Создаем CRUD для типов нарядов
type_views = crud_views(
    model=DutyType,
    form_class=DutyTypeForm,
    template_prefix='type',
    list_url_name='type:type_list',
)

# Экспортируем view-функции
type_list = type_views['list']
type_add = type_views['create']
type_edit = type_views['update']
type_delete = type_views['delete']
type_detail = type_views['detail']