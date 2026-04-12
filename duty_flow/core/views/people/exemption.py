from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from people.models import Person, Exemption
from people.forms import ExemptionForm
from core.services.people_service import PersonService
from access_control.services import AccessManager


@login_required
def exemption_add(request, pk):
    person = get_object_or_404(Person, pk=pk)
    access = AccessManager(request.user)

    if not access.can_person("manage_exemptions", person):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('people:person_detail', pk=person.pk)

    if request.method == 'POST':
        form = ExemptionForm(request.POST)
        if form.is_valid():
            if PersonService.check_exemption_overlap(
                person,
                form.cleaned_data['date_from'],
                form.cleaned_data['date_to']
            ):
                messages.error(request, 'Освобождение пересекается с существующим периодом')
            else:
                try:
                    PersonService.create_exemption(person, form.cleaned_data)
                    messages.success(request, 'Освобождение успешно добавлено')
                    return redirect(f'/persons/{person.pk}/?tab=exemptions')
                except Exception as e:
                    messages.error(request, str(e))
    else:
        form = ExemptionForm()

    return render(request, 'app/people/exemption_form.html', {
        'form': form,
        'person': person,
        'title': f'Добавление освобождения: {person.last_name} {person.first_name}',
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Освобождения сотрудника',
    })


@login_required
def exemption_edit(request, pk, exemption_id):
    person = get_object_or_404(Person, pk=pk)
    exemption = get_object_or_404(Exemption, pk=exemption_id, person=person)
    access = AccessManager(request.user)

    if not access.can_person("manage_exemptions", person):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('people:person_detail', pk=person.pk)

    if request.method == 'POST':
        form = ExemptionForm(request.POST, instance=exemption)
        if form.is_valid():
            if PersonService.check_exemption_overlap(
                person,
                form.cleaned_data['date_from'],
                form.cleaned_data['date_to'],
                exclude_id=exemption.id
            ):
                messages.error(request, 'Освобождение пересекается с существующим периодом')
            else:
                try:
                    PersonService.update_exemption(exemption, form.cleaned_data)
                    messages.success(request, 'Освобождение успешно обновлено')
                    return redirect(f'/persons/{person.pk}/?tab=exemptions')
                except Exception as e:
                    messages.error(request, str(e))
    else:
        form = ExemptionForm(instance=exemption)

    return render(request, 'app/people/exemption_form.html', {
        'form': form,
        'person': person,
        'exemption': exemption,
        'title': 'Редактирование освобождения',
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Освобождения сотрудника',
    })


@login_required
def exemption_delete(request, pk, exemption_id):
    person = get_object_or_404(Person, pk=pk)
    exemption = get_object_or_404(Exemption, pk=exemption_id, person=person)
    access = AccessManager(request.user)

    if not access.can_person("manage_exemptions", person):
        messages.error(request, 'Нет прав для удаления')
        return redirect('people:person_detail', pk=person.pk)

    if request.method == 'POST':
        PersonService.delete_exemption(exemption)
        messages.success(request, 'Освобождение успешно удалено')
        return redirect(f'/persons/{person.pk}/?tab=exemptions')

    return render(request, 'app/people/exemption_delete.html', {
        'exemption': exemption,
        'person': person,
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Удаление освобождения',
    })