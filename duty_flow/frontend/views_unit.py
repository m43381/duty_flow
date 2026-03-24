from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count

from units.models import Unit
from units.forms import UnitForm
from users_app.access_service import AccessService


def list(request):
    """Список/дерево подразделений"""
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        access = AccessService(request.user)
    except Exception as e:
        messages.error(request, f'Ошибка доступа: {str(e)}')
        return redirect('dashboard')
    
    # Получаем видимые подразделения
    visible_units_qs = access.get_visible_units()
    
    # Поиск по названию
    search_query = request.GET.get('search', '').strip()
    if search_query:
        visible_units_qs = visible_units_qs.filter(name__icontains=search_query)
    
    # Получаем права на редактирование и удаление
    editable_units_qs = access.get_editable_units()
    editable_ids = [unit.id for unit in editable_units_qs]
    
    # Получаем права на удаление
    if access.user_level == 0:
        # Академия может удалять всё
        deletable_ids = [unit.id for unit in visible_units_qs]
    else:
        # Остальные могут удалять только дочерние
        deletable_ids = [child.id for child in access.user_unit.children.all()]
    
    # Получаем количество сотрудников
    units_with_counts = visible_units_qs.annotate(people_count=Count('people'))
    
    # Определяем корневые узлы для дерева
    if access.user_level == 0:
        # Академия: все корневые узлы среди видимых
        all_visible_ids = set(unit.id for unit in units_with_counts)
        root_units_data = []
        for unit in units_with_counts:
            if unit.parent is None or unit.parent.id not in all_visible_ids:
                root_units_data.append(unit)
    else:
        # Остальные: только свое подразделение как корень
        root_units_data = [access.user_unit]
    
    # Строим дерево
    def build_tree(unit):
        """Рекурсивное построение дерева"""
        children = []
        for child in unit.children.filter(id__in=visible_units_qs):
            children.append(build_tree(child))
        
        return {
            'id': unit.id,
            'name': unit.name,
            'unit_type': unit.unit_type,
            'level': unit.get_level(),
            'people_count': unit.people_count if hasattr(unit, 'people_count') else unit.people.count(),
            'children': children,
            'can_edit': unit.id in editable_ids,
            'can_delete': unit.id in deletable_ids,
        }
    
    # Строим дерево для каждого корневого узла
    units_tree = []
    for root_unit in root_units_data:
        # Получаем актуальные данные с аннотацией
        try:
            root_with_count = units_with_counts.get(id=root_unit.id)
            units_tree.append(build_tree(root_with_count))
        except Unit.DoesNotExist:
            # Если подразделение не входит в visible_units_qs (например, при поиске)
            # добавляем его без аннотации
            units_tree.append(build_tree(root_unit))
    
    return render(request, 'units/list.html', {
        'units_tree': units_tree,
        'show_as_tree': True,
        'can_add': access.can_create_unit(),
        'active_tab': 'units',
        'title': 'Подразделения',
        'search_query': search_query,
        'user_unit': access.user_unit,
        'user_level': access.user_level,
    })


@login_required
def add(request):
    """Создание подразделения"""
    http_request = request
    
    try:
        access = AccessService(http_request.user)
    except Exception as e:
        messages.error(http_request, f'Ошибка доступа: {str(e)}')
        return redirect('dashboard')
    
    if not access.can_create_unit():
        messages.error(http_request, 'У вас нет прав на создание подразделений')
        return redirect('units:list')
    
    if http_request.method == 'POST':
        form = UnitForm(http_request.POST, user=http_request.user)
        if form.is_valid():
            try:
                unit = form.save()
                messages.success(http_request, f'Подразделение "{unit.name}" создано')
                return redirect('units:detail', pk=unit.pk)
            except IntegrityError as e:
                messages.error(http_request, f'Ошибка при создании подразделения: {str(e)}')
    else:
        parent_id = http_request.GET.get('parent')
        initial = {}
        if parent_id:
            try:
                parent = Unit.objects.get(pk=parent_id)
                # Проверяем, может ли пользователь создавать в этом родителе
                if access.can_create_unit(parent):
                    initial['parent'] = parent
            except Unit.DoesNotExist:
                pass
        form = UnitForm(user=http_request.user, initial=initial)
    
    return render(http_request, 'units/form.html', {
        'form': form,
        'active_tab': 'units',
        'title': 'Создание подразделения',
    })


@login_required
def detail(request, pk):
    """Просмотр подразделения"""
    http_request = request
    
    try:
        access = AccessService(http_request.user)
    except Exception as e:
        messages.error(http_request, f'Ошибка доступа: {str(e)}')
        return redirect('dashboard')
    
    unit = get_object_or_404(Unit, pk=pk)
    
    if not access.can_view_unit(unit):
        messages.error(http_request, 'У вас нет доступа к этому подразделению')
        return redirect('units:list')
    
    employees_count = unit.people.count()
    children_count = unit.children.count()
    can_edit = access.can_edit_unit(unit)
    can_delete = access.can_delete_unit(unit) and unit.people.count() == 0 and children_count == 0
    
    return render(http_request, 'units/detail.html', {
        'unit': unit,
        'employees_count': employees_count,
        'children_count': children_count,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'active_tab': 'units',
        'title': unit.name,
    })


@login_required
def edit(request, pk):
    """Редактирование подразделения"""
    http_request = request
    
    try:
        access = AccessService(http_request.user)
    except Exception as e:
        messages.error(http_request, f'Ошибка доступа: {str(e)}')
        return redirect('dashboard')
    
    unit = get_object_or_404(Unit, pk=pk)
    
    if not access.can_edit_unit(unit):
        messages.error(http_request, 'У вас нет прав на редактирование этого подразделения')
        return redirect('units:list')
    
    if http_request.method == 'POST':
        form = UnitForm(http_request.POST, instance=unit, user=http_request.user)
        if form.is_valid():
            try:
                unit = form.save()
                messages.success(http_request, f'Подразделение "{unit.name}" обновлено')
                return redirect('units:detail', pk=unit.pk)
            except IntegrityError as e:
                messages.error(http_request, f'Ошибка при обновлении подразделения: {str(e)}')
    else:
        form = UnitForm(instance=unit, user=http_request.user)
    
    return render(http_request, 'units/form.html', {
        'form': form,
        'unit': unit,
        'active_tab': 'units',
        'title': 'Редактирование подразделения',
    })


@login_required
def delete(request, pk):
    """Удаление подразделения"""
    http_request = request
    
    try:
        access = AccessService(http_request.user)
    except Exception as e:
        messages.error(http_request, f'Ошибка доступа: {str(e)}')
        return redirect('dashboard')
    
    unit = get_object_or_404(Unit, pk=pk)
    
    if not access.can_delete_unit(unit):
        messages.error(http_request, 'У вас нет прав на удаление этого подразделения')
        return redirect('units:list')
    
    # Проверка: нет дочерних подразделений
    if unit.children.exists():
        messages.error(
            http_request,
            f'Нельзя удалить подразделение "{unit.name}", так как у него '
            f'есть дочерние подразделения. Сначала удалите их.'
        )
        return redirect('units:detail', pk=unit.pk)
    
    # Проверка: нет сотрудников
    if unit.people.count() > 0:
        messages.error(
            http_request,
            f'Нельзя удалить подразделение "{unit.name}", так как в нем '
            f'есть сотрудники ({unit.people.count()} чел.). '
            f'Сначала переведите или удалите сотрудников.'
        )
        return redirect('units:detail', pk=unit.pk)
    
    # Проверка: нет планов
    try:
        from duty_plans.models import DayPlan
        if DayPlan.objects.filter(unit=unit).exists():
            messages.error(
                http_request,
                f'Нельзя удалить подразделение "{unit.name}", так как для него '
                f'существуют планы нарядов.'
            )
            return redirect('units:detail', pk=unit.pk)
    except ImportError:
        pass
    
    if http_request.method == 'POST':
        unit_name = unit.name
        unit.delete()
        messages.success(http_request, f'Подразделение "{unit_name}" удалено')
        return redirect('units:list')
    
    return render(http_request, 'units/delete.html', {
        'unit': unit,
        'active_tab': 'units',
        'title': 'Удаление подразделения',
    })