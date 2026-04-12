from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from people.models import Person, DutyClearance
from people.forms import DutyClearanceForm
from core.services.people_service import PersonService
from access_control.services import AccessManager
from access_control.services.duty_type_labels import build_duty_type_label


@login_required
def clearance_add(request, pk):
    person = get_object_or_404(Person, pk=pk)
    access = AccessManager(request.user)

    if not access.can_person("manage_clearances", person):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('people:person_detail', pk=person.pk)

    if request.method == 'POST':
        form = DutyClearanceForm(request.POST, person=person)

        allowed_qs = access.allowed_duty_types_for_clearance()
        form.fields['duty_type'].queryset = allowed_qs
        form.fields['duty_type'].label_from_instance = build_duty_type_label

        if form.is_valid():
            duty_type = form.cleaned_data['duty_type']
            PersonService.create_clearance(person, duty_type)
            messages.success(request, 'Допуск успешно добавлен')
            return redirect(f'/persons/{person.pk}/?tab=clearances')
    else:
        form = DutyClearanceForm(person=person)

        allowed_qs = access.allowed_duty_types_for_clearance()
        form.fields['duty_type'].queryset = allowed_qs
        form.fields['duty_type'].label_from_instance = build_duty_type_label

    return render(request, 'app/people/clearance_form.html', {
        'form': form,
        'person': person,
        'title': f'Добавление допуска: {person.last_name} {person.first_name}',
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Допуски сотрудника',
    })


@login_required
def clearance_delete(request, pk, clearance_id):
    person = get_object_or_404(Person, pk=pk)
    clearance = get_object_or_404(DutyClearance, pk=clearance_id, person=person)
    access = AccessManager(request.user)

    if not access.can_person("manage_clearances", person):
        messages.error(request, 'Нет прав для удаления')
        return redirect('people:person_detail', pk=person.pk)

    if request.method == 'POST':
        PersonService.delete_clearance(clearance)
        messages.success(request, 'Допуск успешно удален')
        return redirect(f'/persons/{person.pk}/?tab=clearances')

    return render(request, 'app/people/clearance_delete.html', {
        'clearance': clearance,
        'person': person,
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Удаление допуска',
    })