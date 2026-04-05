"""
Сервис для работы с типами нарядов
"""
from duty_types.models import DutyType


class DutyTypeService:
    """Сервис для работы с типами нарядов"""
    
    @staticmethod
    def get_user_duty_types(user):
        """Возвращает типы нарядов, доступные пользователю"""
        from users_app.access_service import AccessService
        access = AccessService(user)
        return DutyType.objects.filter(created_by_unit=access.user_unit).order_by('name')
    
    @staticmethod
    def can_edit(user, duty_type):
        """Проверяет, может ли пользователь редактировать тип наряда"""
        from users_app.access_service import AccessService
        access = AccessService(user)
        return duty_type.created_by_unit == access.user_unit
    
    @staticmethod
    def create_duty_type(form_data, user):
        """Создаёт тип наряда"""
        from users_app.access_service import AccessService
        access = AccessService(user)
        
        duty_type = DutyType(
            name=form_data['name'],
            description=form_data.get('description', ''),
            required_people=form_data.get('required_people', 1),
            created_by_unit=access.user_unit,
            unit=form_data.get('unit')
        )
        duty_type.save()
        return duty_type
    
    @staticmethod
    def update_duty_type(duty_type, form_data):
        """Обновляет тип наряда"""
        duty_type.name = form_data['name']
        duty_type.description = form_data.get('description', '')
        duty_type.required_people = form_data.get('required_people', 1)
        duty_type.unit = form_data.get('unit')
        duty_type.save()
        return duty_type