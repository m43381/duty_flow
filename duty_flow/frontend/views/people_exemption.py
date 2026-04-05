from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from people.models import Person, Exemption
from people.forms import ExemptionForm
from users_app.access_service import AccessService

@login_required
def exemption_add(request, pk):
    """Добавление освобождения для сотрудника"""
    person = get_object_or_404(Person, pk=pk)
    access = AccessService(request.user)
    
    if not access.can_edit_object(person):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('person:person_detail', pk=person.pk)
    
    if request.method == 'POST':
        form = ExemptionForm(request.POST)
        if form.is_valid():
            exemption = form.save(commit=False)
            exemption.person = person
            
            # Валидация пересечения дат
            existing = Exemption.objects.filter(
                person=person,
                date_from__lte=exemption.date_to,
                date_to__gte=exemption.date_from
            )
            
            if existing.exists():
                messages.error(request, 'Освобождение пересекается с существующим периодом')
                return render(request, 'person/exemption_form.html', {
                    'form': form,
                    'person': person,
                    'title': f'Добавление освобождения: {person.last_name} {person.first_name}',
                })
            
            try:
                exemption.full_clean()
                exemption.save()
                messages.success(request, 'Освобождение успешно добавлено')
                return redirect(f'/persons/{person.pk}/?tab=exemptions')
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
    else:
        form = ExemptionForm()
    
    return render(request, 'person/exemption_form.html', {
        'form': form,
        'person': person,
        'title': f'Добавление освобождения: {person.last_name} {person.first_name}',
    })

@login_required
def exemption_edit(request, pk, exemption_id):
    """Редактирование освобождения"""
    person = get_object_or_404(Person, pk=pk)
    exemption = get_object_or_404(Exemption, pk=exemption_id, person=person)
    access = AccessService(request.user)
    
    if not access.can_edit_object(person):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('person:person_detail', pk=person.pk)
    
    if request.method == 'POST':
        form = ExemptionForm(request.POST, instance=exemption)
        if form.is_valid():
            # Валидация пересечения дат (исключая текущее освобождение)
            existing = Exemption.objects.filter(
                person=person,
                date_from__lte=form.cleaned_data['date_to'],
                date_to__gte=form.cleaned_data['date_from']
            ).exclude(pk=exemption.pk)
            
            if existing.exists():
                messages.error(request, 'Освобождение пересекается с существующим периодом')
                return render(request, 'person/exemption_form.html', {
                    'form': form,
                    'person': person,
                    'exemption': exemption,
                    'title': 'Редактирование освобождения',
                })
            
            try:
                form.save()
                messages.success(request, 'Освобождение успешно обновлено')
                return redirect(f'/persons/{person.pk}/?tab=exemptions')
            except ValidationError as e:
                for field, errors in e.message_dict.items():
                    for error in errors:
                        form.add_error(field, error)
    else:
        form = ExemptionForm(instance=exemption)
    
    return render(request, 'person/exemption_form.html', {
        'form': form,
        'person': person,
        'exemption': exemption,
        'title': 'Редактирование освобождения',
    })

@login_required
def exemption_delete(request, pk, exemption_id):
    """Удаление освобождения"""
    person = get_object_or_404(Person, pk=pk)
    exemption = get_object_or_404(Exemption, pk=exemption_id, person=person)
    access = AccessService(request.user)
    
    if not access.can_edit_object(person):
        messages.error(request, 'Нет прав для удаления')
        return redirect('person:person_detail', pk=person.pk)
    
    if request.method == 'POST':
        exemption.delete()
        messages.success(request, 'Освобождение успешно удалено')
        return redirect(f'/persons/{person.pk}/?tab=exemptions')
    
    return render(request, 'person/exemption_confirm_delete.html', {
        'exemption': exemption,
        'person': person,
    })