from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.apps import apps
from .models import Person
from .forms import PersonForm

@login_required
def person_list(request):
    persons = Person.objects.all().select_related('unit')
    return render(request, 'people/person_list.html', {
        'page_title': 'Сотрудники',
        'active_tab': 'people',
        'persons': persons
    })

@login_required
def person_create(request):
    if request.method == 'POST':
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save()
            messages.success(request, f'Сотрудник успешно добавлен')
            return redirect('people:person_list')
    else:
        form = PersonForm()
    
    return render(request, 'people/person_form.html', {
        'page_title': 'Добавление сотрудника',
        'active_tab': 'people',
        'form': form,
        'action': 'create'
    })

@login_required
def person_update(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == 'POST':
        form = PersonForm(request.POST, instance=person)
        if form.is_valid():
            person = form.save()
            messages.success(request,'Данные сотрудника {person.full_name} обновлены')
            return redirect('people:person_list')
    else:
        form = PersonForm(instance=person)
    
    return render(request, 'people/person_form.html', {
        'page_title': 'Редактирование сотрудника',
        'active_tab': 'people',
        'form': form,
        'person': person,
        'action': 'update'
    })

@login_required
def person_delete(request, pk):
    person = get_object_or_404(Person, pk=pk)
    if request.method == 'POST':
        person_name = person.full_name
        person.delete()
        messages.success(request,'Сотрудник успешно удален')
        return redirect('people:person_list')
    
    return render(request, 'people/person_confirm_delete.html', {
        'page_title': 'Удаление сотрудника',
        'active_tab': 'people',
        'person': person
    })

@login_required
def person_detail(request, pk):
    person = get_object_or_404(Person.objects.select_related('unit'), pk=pk)
    return render(request, 'people/person_detail.html', {
        'page_title': f'Сотрудник: {person.full_name}',
        'active_tab': 'people',
        'person': person
    })