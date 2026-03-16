from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from people.models import Person, Exemption
from people.forms import ExemptionForm
from users_app.access_service import AccessService

@login_required
def exemption_add(request, pk):
    """
    Добавление освобождения для сотрудника
    URL: /persons/<pk>/exemption/add/
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
        form = ExemptionForm(request.POST)
        if form.is_valid():
            exemption = form.save(commit=False)
            exemption.person = person
            exemption.save()
            messages.success(request, 'Освобождение успешно добавлено')
            return redirect(f'{request.path}?tab=exemptions')
    else:
        form = ExemptionForm()
    
    return render(request, 'person/exemption_form.html', {
        'form': form,
        'person': person,
        'title': f'Добавление освобождения: {person.last_name} {person.first_name}',
    })

@login_required
def exemption_edit(request, pk, exemption_id):
    """
    Редактирование освобождения
    URL: /persons/<pk>/exemption/<exemption_id>/edit/
    """
    # Получаем сотрудника и убеждаемся, что освобождение принадлежит ему
    person = get_object_or_404(Person, pk=pk)
    exemption = get_object_or_404(Exemption, pk=exemption_id, person=person)
    
    # Проверяем права
    access = AccessService(request.user)
    if not access.can_edit_object(person):
        messages.error(request, 'У вас нет прав для редактирования этого сотрудника')
        return redirect('person:person_detail', pk=person.pk)
    
    # Обработка формы
    if request.method == 'POST':
        form = ExemptionForm(request.POST, instance=exemption)
        if form.is_valid():
            form.save()
            messages.success(request, 'Освобождение успешно обновлено')
            return redirect(f'/persons/{person.pk}/?tab=exemptions')
    else:
        form = ExemptionForm(instance=exemption)
    
    return render(request, 'person/exemption_form.html', {
        'form': form,
        'person': person,
        'exemption': exemption,
        'title': f'Редактирование освобождения',
    })

@login_required
def exemption_delete(request, pk, exemption_id):
    """
    Удаление освобождения
    URL: /persons/<pk>/exemption/<exemption_id>/delete/
    """
    # Получаем сотрудника и убеждаемся, что освобождение принадлежит ему
    person = get_object_or_404(Person, pk=pk)
    exemption = get_object_or_404(Exemption, pk=exemption_id, person=person)
    
    # Проверяем права
    access = AccessService(request.user)
    if not access.can_edit_object(person):
        messages.error(request, 'У вас нет прав для удаления')
        return redirect('person:person_detail', pk=person.pk)
    
    # Подтверждение удаления
    if request.method == 'POST':
        exemption.delete()
        messages.success(request, 'Освобождение успешно удалено')
        return redirect(f'/persons/{person.pk}/?tab=exemptions')
    
    return render(request, 'person/exemption_confirm_delete.html', {
        'exemption': exemption,
        'person': person,
    })