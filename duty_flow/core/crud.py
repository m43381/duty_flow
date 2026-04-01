from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from users_app.access_service import AccessService


def crud_views(model, form_class, template_prefix,
               list_url_name=None, 
               extra_context=None,
               has_unit_field=True):
    """
    Универсальная фабрика CRUD view-функций
    
    Args:
        model: Django модель
        form_class: Django форма
        template_prefix: префикс шаблонов
        extra_context: дополнительный контекст
        has_unit_field: имеет ли модель поле 'unit' для фильтрации
    """
    
    if list_url_name is None:
        list_url_name = f'{template_prefix}_list'
    
    @login_required
    def list_view(request):
        """Список объектов"""
        access = AccessService(request.user)
        
        # Получаем queryset с фильтрацией по подразделениям
        if has_unit_field:
            queryset = access.get_visible_queryset(model.objects.all())
            # Исправлено: передаем объект Unit, а не ID
            can_add = access.can_create_in_unit(access.user_unit)
        else:
            queryset = model.objects.all()
            can_add = True
        
        # Поиск
        search_query = request.GET.get('search', '')
        if search_query and hasattr(model, 'name'):
            queryset = queryset.filter(name__icontains=search_query)
        
        # Пагинация
        paginator = Paginator(queryset, 50)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'items': page_obj,
            'active_tab': template_prefix,
            'title': f'Список {model._meta.verbose_name_plural}',
            'can_add': can_add,
            'search_query': search_query,
            'filter_context': access.get_filter_context() if has_unit_field else None,
        }
        
        if extra_context:
            context.update(extra_context)
        
        return render(request, f'{template_prefix}/list.html', context)
    
    @login_required
    def create_view(request):
        """Создание объекта"""
        access = AccessService(request.user)
        
        # Проверка прав на создание
        if has_unit_field:
            # Исправлено: передаем объект Unit, а не ID
            if not access.can_create_in_unit(access.user_unit):
                messages.error(request, 'Нет прав для создания')
                return redirect(list_url_name)
        
        if request.method == 'POST':
            form = form_class(request.POST, user=request.user)
            if form.is_valid():
                obj = form.save(commit=False)
                if has_unit_field:
                    obj.unit = access.user_unit
                obj.save()
                messages.success(request, f'{model._meta.verbose_name} создан')
                return redirect(list_url_name)
        else:
            form = form_class(user=request.user)
        
        return render(request, f'{template_prefix}/form.html', {
            'form': form,
            'active_tab': template_prefix,
            'title': f'Добавление {model._meta.verbose_name}',
        })
    
    @login_required
    def update_view(request, pk):
        """Редактирование объекта"""
        access = AccessService(request.user)
        obj = get_object_or_404(model, pk=pk)
        
        # Проверка прав на редактирование
        if has_unit_field:
            if not access.can_edit_object(obj):
                messages.error(request, 'Нет прав для редактирования')
                return redirect(list_url_name)
        
        if request.method == 'POST':
            form = form_class(request.POST, instance=obj, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, f'{model._meta.verbose_name} обновлен')
                return redirect(list_url_name)
        else:
            form = form_class(instance=obj, user=request.user)
        
        return render(request, f'{template_prefix}/form.html', {
            'form': form,
            'item': obj,
            'active_tab': template_prefix,
            'title': f'Редактирование {obj}',
        })
    
    @login_required
    def delete_view(request, pk):
        """Удаление объекта"""
        access = AccessService(request.user)
        obj = get_object_or_404(model, pk=pk)
        
        # Проверка прав на удаление
        if has_unit_field:
            if not access.can_edit_object(obj):
                messages.error(request, 'Нет прав для удаления')
                return redirect(list_url_name)
        
        if request.method == 'POST':
            obj.delete()
            messages.success(request, f'{model._meta.verbose_name} удален')
            return redirect(list_url_name)
        
        return render(request, f'{template_prefix}/delete.html', {
            'item': obj,
            'active_tab': template_prefix,
            'title': f'Удаление {obj}',
        })
    
    @login_required
    def detail_view(request, pk):
        """Просмотр объекта"""
        access = AccessService(request.user)
        obj = get_object_or_404(model, pk=pk)
        
        # Проверка прав на просмотр
        if has_unit_field:
            if not access.can_view_object(obj):
                messages.error(request, 'Нет прав для просмотра')
                return redirect(list_url_name)
        
        context = {
            'item': obj,
            'active_tab': template_prefix,
            'title': f'Просмотр {obj}',
        }
        
        if has_unit_field:
            context['can_edit'] = access.can_edit_object(obj)
            context['can_delete'] = access.can_edit_object(obj)
        
        if extra_context:
            context.update(extra_context)
        
        return render(request, f'{template_prefix}/detail.html', context)
    
    return {
        'list': list_view,
        'create': create_view,
        'update': update_view,
        'delete': delete_view,
        'detail': detail_view,
    }