from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from people.models import Person, DutyClearance
from people.forms import DutyClearanceForm
from users_app.access_service import AccessService

@login_required
def clearance_add(request, pk):
    """
    Добавление допуска для сотрудника
    URL: /persons/<pk>/clearance/add/
    """
    # Получаем сотрудника или 404
    person = get_object_or_404(Person, pk=pk)
    
    # Проверяем права
    access = AccessService(request.user)
    if not access.can_edit_object(person):
        messages.error(request, 'У вас нет прав для редактирования этого сотрудника')
        return redirect('person:person_detail', pk=person.pk)
    
    # Обработка формы
    if request.method == 'POST':
        form = DutyClearanceForm(request.POST)
        if form.is_valid():
            clearance = form.save(commit=False)
            clearance.person = person
            clearance.save()
            messages.success(request, 'Допуск успешно добавлен')
            return redirect(f'/persons/{person.pk}/?tab=clearances')
    else:
        form = DutyClearanceForm()
    
    return render(request, 'person/clearance_form.html', {
        'form': form,
        'person': person,
        'title': f'Добавление допуска: {person.last_name} {person.first_name}',
    })

@login_required
def clearance_delete(request, pk, clearance_id):
    """
    Удаление допуска
    URL: /persons/<pk>/clearance/<clearance_id>/delete/
    """
    # Получаем сотрудника и убеждаемся, что допуск принадлежит ему
    person = get_object_or_404(Person, pk=pk)
    clearance = get_object_or_404(DutyClearance, pk=clearance_id, person=person)
    
    # Проверяем права
    access = AccessService(request.user)
    if not access.can_edit_object(person):
        messages.error(request, 'У вас нет прав для удаления')
        return redirect('person:person_detail', pk=person.pk)
    
    # Подтверждение удаления
    if request.method == 'POST':
        clearance.delete()
        messages.success(request, 'Допуск успешно удален')
        return redirect(f'/persons/{person.pk}/?tab=clearances')
    
    return render(request, 'person/clearance_confirm_delete.html', {
        'clearance': clearance,
        'person': person,
    })