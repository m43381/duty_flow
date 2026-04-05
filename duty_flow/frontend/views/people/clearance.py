from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from people.models import Person, DutyClearance
from people.forms import DutyClearanceForm
from users_app.access_service import AccessService
from frontend.services.person_service import PersonService


@login_required
def clearance_add(request, pk):
    person = get_object_or_404(Person, pk=pk)
    access = AccessService(request.user)
    
    if not access.can_edit_object(person):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('person:person_detail', pk=person.pk)
    
    if request.method == 'POST':
        form = DutyClearanceForm(request.POST, person=person)
        if form.is_valid():
            duty_type = form.cleaned_data['duty_type']
            PersonService.create_clearance(person, duty_type)
            messages.success(request, 'Допуск успешно добавлен')
            return redirect(f'/persons/{person.pk}/?tab=clearances')
    else:
        form = DutyClearanceForm(person=person)
    
    return render(request, 'person/clearance_form.html', {
        'form': form,
        'person': person,
        'title': f'Добавление допуска: {person.last_name} {person.first_name}',
    })


@login_required
def clearance_delete(request, pk, clearance_id):
    person = get_object_or_404(Person, pk=pk)
    clearance = get_object_or_404(DutyClearance, pk=clearance_id, person=person)
    access = AccessService(request.user)
    
    if not access.can_edit_object(person):
        messages.error(request, 'Нет прав для удаления')
        return redirect('person:person_detail', pk=person.pk)
    
    if request.method == 'POST':
        PersonService.delete_clearance(clearance)
        messages.success(request, 'Допуск успешно удален')
        return redirect(f'/persons/{person.pk}/?tab=clearances')
    
    return render(request, 'person/clearance_confirm_delete.html', {
        'clearance': clearance,
        'person': person,
    })