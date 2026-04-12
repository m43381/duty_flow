"""
Сервис для работы с подразделениями и их типами
"""
from django.db.models import Count

from units.models import Unit, UnitType
from duty_plans.models import DayPlan


class UnitService:
    """Сервис для работы с подразделениями"""

    @staticmethod
    def get_units_with_counts(units_qs):
        """Добавляет количество сотрудников к каждому подразделению"""
        return units_qs.annotate(people_count=Count("people"))

    @staticmethod
    def build_unit_tree(units_qs, root_units, editable_ids, deletable_ids):
        """Рекурсивно строит дерево подразделений"""
        units_dict = {u.id: u for u in units_qs}

        def build_tree(unit):
            children = []
            for child in unit.children.filter(id__in=units_dict.keys()):
                children.append(build_tree(child))

            return {
                "id": unit.id,
                "name": unit.name,
                "unit_type": unit.unit_type,
                "level": unit.get_level(),
                "people_count": getattr(unit, "people_count", unit.people.count()),
                "children": children,
                "can_edit": unit.id in editable_ids,
                "can_delete": unit.id in deletable_ids,
            }

        tree = []
        for root in root_units:
            tree.append(build_tree(root))

        return tree

    @staticmethod
    def get_root_units(units_qs, user_level, user_unit):
        """Определяет корневые узлы для дерева"""
        if user_level == 0:
            all_visible_ids = set(unit.id for unit in units_qs)
            return [unit for unit in units_qs if unit.parent is None or unit.parent.id not in all_visible_ids]
        return [user_unit] if user_unit else []

    @staticmethod
    def can_delete_unit(unit, user):
        """Проверяет, можно ли удалить подразделение"""
        from access_control.services import AccessManager
        access = AccessManager(user)

        if not access.can_unit("delete", unit):
            return False, "У вас нет прав на удаление этого подразделения"

        if unit.children.exists():
            return False, "Нельзя удалить подразделение, так как у него есть дочерние подразделения. Сначала удалите их."

        if unit.people.count() > 0:
            return False, f"Нельзя удалить подразделение, так как в нем есть сотрудники ({unit.people.count()} чел.). Сначала переведите или удалите сотрудников."

        if DayPlan.objects.filter(unit=unit).exists():
            return False, "Нельзя удалить подразделение, так как для него существуют планы нарядов."

        return True, ""

    @staticmethod
    def get_deletable_ids(units_qs, user):
        """Возвращает список ID подразделений, которые пользователь может удалить"""
        from access_control.services import AccessManager
        access = AccessManager(user)
        return [unit.id for unit in units_qs if access.can_unit("delete", unit)]

    @staticmethod
    def get_editable_ids(units_qs, user):
        """Возвращает список ID подразделений, которые пользователь может редактировать"""
        from access_control.services import AccessManager
        access = AccessManager(user)
        return [unit.id for unit in units_qs if access.can_unit("update", unit)]


class UnitTypeService:
    """Сервис для работы с типами подразделений"""

    @staticmethod
    def can_manage(user):
        """Проверяет, может ли пользователь управлять типами (только академия)"""
        from users_app.access_service import AccessService
        access = AccessService(user)
        return access.user_level == 0

    @staticmethod
    def get_usage_stats(unit_type):
        """Возвращает статистику использования типа"""
        units_count = unit_type.units.count()
        users_count = sum(u.users.count() for u in unit_type.units.all())
        return units_count, users_count

    @staticmethod
    def can_delete_type(unit_type):
        """Проверяет, можно ли удалить тип подразделения"""
        units_count = unit_type.units.count()
        if units_count > 0:
            return False, f"Нельзя удалить тип, так как существуют подразделения этого типа ({units_count} шт.). Сначала удалите или измените тип у подразделений."
        return True, ""