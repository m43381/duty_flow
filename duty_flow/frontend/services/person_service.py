"""
Сервис для работы с сотрудниками, освобождениями и допусками
"""
from django.core.exceptions import ValidationError
from people.models import Person, Exemption, DutyClearance


class PersonService:
    """Сервис для работы с сотрудниками"""
    
    @staticmethod
    def get_person_with_access_check(pk, user, action='view'):
        """Получает сотрудника и проверяет права"""
        from users_app.access_service import AccessService
        access = AccessService(user)
        person = Person.objects.get(pk=pk)
        
        if action == 'view':
            has_access = access.can_view_object(person)
        else:
            has_access = access.can_edit_object(person)
        
        return person, has_access
    
    @staticmethod
    def check_exemption_overlap(person, date_from, date_to, exclude_id=None):
        """Проверяет пересечение освобождений по датам"""
        queryset = Exemption.objects.filter(
            person=person,
            date_from__lte=date_to,
            date_to__gte=date_from
        )
        if exclude_id:
            queryset = queryset.exclude(pk=exclude_id)
        return queryset.exists()
    
    @staticmethod
    def create_exemption(person, form_data):
        """Создаёт освобождение"""
        exemption = Exemption(
            person=person,
            reason=form_data['reason'],
            date_from=form_data['date_from'],
            date_to=form_data['date_to'],
            comment=form_data.get('comment', '')
        )
        exemption.full_clean()
        exemption.save()
        return exemption
    
    @staticmethod
    def update_exemption(exemption, form_data):
        """Обновляет освобождение"""
        exemption.reason = form_data['reason']
        exemption.date_from = form_data['date_from']
        exemption.date_to = form_data['date_to']
        exemption.comment = form_data.get('comment', '')
        exemption.full_clean()
        exemption.save()
        return exemption
    
    @staticmethod
    def delete_exemption(exemption):
        """Удаляет освобождение"""
        exemption.delete()
    
    @staticmethod
    def create_clearance(person, duty_type):
        """Создаёт допуск"""
        clearance, created = DutyClearance.objects.get_or_create(
            person=person,
            duty_type=duty_type
        )
        return clearance
    
    @staticmethod
    def delete_clearance(clearance):
        """Удаляет допуск"""
        clearance.delete()