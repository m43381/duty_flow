from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
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
    
    def get_access_service(request):
        return AccessService(request.user)
    
    if list_url_name is None:
        list_url_name = f'{template_prefix}_list'
    
    @login_required
    def list_view(request):
        """Список объектов"""
        access = get_access_service(request)
        
        if has_unit_field:
            queryset = access.get_visible_queryset(model.objects.all())
        else:
            queryset = model.objects.all()
        
        # Применяем фильтры из запроса
        if has_unit_field and 'unit' in request.GET and request.GET['unit']:
            unit_id = request.GET['unit']
            if unit_id and int(unit_id) in [u.id for u in access.get_visible_units()]:
                queryset = queryset.filter(unit_id=unit_id)
        
        context = {
            'items': queryset,
            'active_tab': template_prefix,
            'title': f'Список {model._meta.verbose_name_plural}',
            'can_add': access.can_create_in_unit(access.user_unit.id) if has_unit_field else True,
            'filter_context': access.get_filter_context() if has_unit_field else None,
        }
        
        if extra_context:
            context.update(extra_context)
        
        return render(request, f'{template_prefix}/list.html', context)
    
    @login_required
    def create_view(request):
        """Создание объекта"""
        access = get_access_service(request)
        
        if has_unit_field and not access.can_create_in_unit(access.user_unit.id):
            messages.error(request, 'Нет прав для создания')
            return redirect(list_url_name)
        
        if request.method == 'POST':
            form = form_class(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                if has_unit_field:
                    obj.unit = access.user_unit
                obj.save()
                messages.success(request, f'{model._meta.verbose_name} создан')
                return redirect(list_url_name)
        else:
            form = form_class()
        
        return render(request, f'{template_prefix}/form.html', {
            'form': form,
            'active_tab': template_prefix,
            'title': f'Добавление {model._meta.verbose_name}',
        })
    
    @login_required
    def update_view(request, pk):
        """Редактирование объекта"""
        access = get_access_service(request)
        obj = get_object_or_404(model, pk=pk)
        
        if has_unit_field and not access.can_edit_object(obj):
            messages.error(request, 'Нет прав для редактирования')
            return redirect(list_url_name)
        
        if request.method == 'POST':
            form = form_class(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                messages.success(request, f'{model._meta.verbose_name} обновлен')
                return redirect(list_url_name)
        else:
            form = form_class(instance=obj)
        
        return render(request, f'{template_prefix}/form.html', {
            'form': form,
            'item': obj,
            'active_tab': template_prefix,
            'title': f'Редактирование {obj}',
        })
    
    @login_required
    def delete_view(request, pk):
        """Удаление объекта"""
        access = get_access_service(request)
        obj = get_object_or_404(model, pk=pk)
        
        if has_unit_field and not access.can_edit_object(obj):
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
        access = get_access_service(request)
        obj = get_object_or_404(model, pk=pk)
        
        if has_unit_field and not access.can_view_object(obj):
            messages.error(request, 'Нет прав для просмотра')
            return redirect(list_url_name)
        
        return render(request, f'{template_prefix}/detail.html', {
            'item': obj,
            'active_tab': template_prefix,
            'title': f'Просмотр {obj}',
            'can_edit': access.can_edit_object(obj) if has_unit_field else True,
        })
    
    return {
        'list': list_view,
        'create': create_view,
        'update': update_view,
        'delete': delete_view,
        'detail': detail_view,
    }