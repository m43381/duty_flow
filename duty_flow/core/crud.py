from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from functools import wraps
from users_app.access_service import AccessService

def crud_views(model, form_class, template_prefix, 
               extra_context=None):
    """
    Универсальная фабрика CRUD view-функций
    
    Args:
        model: Django модель (должна иметь поле 'unit')
        form_class: Django форма
        template_prefix: префикс шаблонов
        extra_context: дополнительный контекст
    """
    
    def get_access_service(request):
        return AccessService(request.user)
    
    @login_required
    def list_view(request):
        """Список объектов"""
        access = get_access_service(request)
        queryset = access.get_visible_queryset(model.objects.all())
        
        # Применяем фильтры из запроса
        if 'unit' in request.GET and request.GET['unit']:
            # Проверяем, что запрошенное подразделение доступно для просмотра
            unit_id = request.GET['unit']
            if unit_id and int(unit_id) in [u.id for u in access.get_visible_units()]:
                queryset = queryset.filter(unit_id=unit_id)
        
        context = {
            'items': queryset,
            'active_tab': template_prefix,
            'title': f'Список {model._meta.verbose_name_plural}',
            'can_add': access.can_create_in_unit(access.user_unit.id),
            'filter_context': access.get_filter_context(),
        }
        
        if extra_context:
            context.update(extra_context)
        
        return render(request, f'{template_prefix}/list.html', context)
    
    @login_required
    def create_view(request):
        """Создание объекта"""
        access = get_access_service(request)
        
        if not access.can_create_in_unit(access.user_unit.id):
            messages.error(request, 'Нет прав для создания')
            return redirect(f'{template_prefix}_list')
        
        if request.method == 'POST':
            form = form_class(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.unit = access.user_unit  # Всегда создаём в своём подразделении
                obj.save()
                messages.success(request, f'{model._meta.verbose_name} создан')
                return redirect(f'{template_prefix}_list')
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
        
        if not access.can_edit_object(obj):
            messages.error(request, 'Нет прав для редактирования')
            return redirect(f'{template_prefix}_list')
        
        if request.method == 'POST':
            form = form_class(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                messages.success(request, f'{model._meta.verbose_name} обновлен')
                return redirect(f'{template_prefix}_list')
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
        
        if not access.can_edit_object(obj):
            messages.error(request, 'Нет прав для удаления')
            return redirect(f'{template_prefix}_list')
        
        if request.method == 'POST':
            obj.delete()
            messages.success(request, f'{model._meta.verbose_name} удален')
            return redirect(f'{template_prefix}_list')
        
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
        
        if not access.can_view_object(obj):
            messages.error(request, 'Нет прав для просмотра')
            return redirect(f'{template_prefix}_list')
        
        return render(request, f'{template_prefix}/detail.html', {
            'item': obj,
            'active_tab': template_prefix,
            'title': f'Просмотр {obj}',
            'can_edit': access.can_edit_object(obj),
        })
    
    return {
        'list': list_view,
        'create': create_view,
        'update': update_view,
        'delete': delete_view,
        'detail': detail_view,
    }