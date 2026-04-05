from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from people.models import Person, Exemption, DutyClearance
from people.forms import PersonForm
from users_app.access_service import AccessService


@login_required
def person_list(request):
    access = AccessService(request.user)
    people = access.get_visible_queryset(Person.objects.all())
    
    search_query = request.GET.get('search', '')
    if search_query:
        people = people.filter(
            last_name__icontains=search_query
        ) | people.filter(
            first_name__icontains=search_query
        )
    
    return render(request, 'person/list.html', {
        'items': people,
        'active_tab': 'person',
        'title': 'Сотрудники',
        'can_add': access.can_create_in_unit(access.user_unit),
        'search_query': search_query,
    })


@login_required
def person_add(request):
    access = AccessService(request.user)
    
    if not access.can_create_in_unit(access.user_unit):
        messages.error(request, 'Нет прав для создания')
        return redirect('person:person_list')
    
    if request.method == 'POST':
        form = PersonForm(request.POST, user=request.user)
        if form.is_valid():
            person = form.save(commit=False)
            person.unit = access.user_unit
            person.save()
            messages.success(request, f'Сотрудник {person} создан')
            return redirect('person:person_detail', pk=person.pk)
    else:
        form = PersonForm(user=request.user)
    
    return render(request, 'person/form.html', {
        'form': form,
        'active_tab': 'person',
        'title': 'Добавление сотрудника'
    })


@login_required
def person_detail(request, pk):
    access = AccessService(request.user)
    person = get_object_or_404(Person, pk=pk)
    
    if not access.can_view_object(person):
        messages.error(request, 'Нет прав для просмотра')
        return redirect('person:person_list')
    
    tab = request.GET.get('tab', 'info')
    
    context = {
        'person': person,
        'can_edit': access.can_edit_object(person),
        'active_tab': 'person',
        'title': f'Сотрудник: {person.last_name} {person.first_name}',
        'tab': tab,
    }
    
    if tab == 'exemptions':
        context['exemptions'] = Exemption.objects.filter(person=person).order_by('-date_from')
    elif tab == 'clearances':
        context['clearances'] = DutyClearance.objects.filter(person=person).select_related('duty_type')
    
    return render(request, 'person/detail.html', context)


@login_required
def person_edit(request, pk):
    access = AccessService(request.user)
    person = get_object_or_404(Person, pk=pk)
    
    if not access.can_edit_object(person):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('person:person_list')
    
    if request.method == 'POST':
        form = PersonForm(request.POST, instance=person, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сотрудник обновлён')
            return redirect('person:person_detail', pk=person.pk)
    else:
        form = PersonForm(instance=person, user=request.user)
    
    return render(request, 'person/form.html', {
        'form': form,
        'item': person,
        'active_tab': 'person',
        'title': f'Редактирование {person}'
    })


@login_required
def person_delete(request, pk):
    access = AccessService(request.user)
    person = get_object_or_404(Person, pk=pk)
    
    if not access.can_edit_object(person):
        messages.error(request, 'Нет прав для удаления')
        return redirect('person:person_list')
    
    if request.method == 'POST':
        person.delete()
        messages.success(request, 'Сотрудник удалён')
        return redirect('person:person_list')
    
    return render(request, 'person/delete.html', {
        'item': person,
        'active_tab': 'person',
        'title': 'Удаление сотрудника'
    })