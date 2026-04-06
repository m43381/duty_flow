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

    search_query = request.GET.get('q', '').strip()
    if search_query:
        people = people.filter(
            last_name__icontains=search_query
        ) | people.filter(
            first_name__icontains=search_query
        )

    return render(request, 'app/people/list.html', {
        'people': people,
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Список сотрудников и переход в карточки',
        'can_add': access.can_create_in_unit(access.user_unit),
        'can_edit': True,
        'search_query': search_query,
    })


@login_required
def person_add(request):
    access = AccessService(request.user)

    if not access.can_create_in_unit(access.user_unit):
        messages.error(request, 'Нет прав для создания')
        return redirect('people:person_list')

    if request.method == 'POST':
        form = PersonForm(request.POST, user=request.user)
        if form.is_valid():
            person = form.save(commit=False)
            person.unit = access.user_unit
            person.save()
            messages.success(request, f'Сотрудник {person} создан')
            return redirect('people:person_detail', pk=person.pk)
    else:
        form = PersonForm(user=request.user)

    return render(request, 'app/people/form.html', {
        'form': form,
        'person': None,
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Добавление сотрудника',
        'title': 'Добавить сотрудника',
    })


@login_required
def person_detail(request, pk):
    access = AccessService(request.user)
    person = get_object_or_404(Person, pk=pk)

    if not access.can_view_object(person):
        messages.error(request, 'Нет прав для просмотра')
        return redirect('people:person_list')

    tab = request.GET.get('tab', 'info')

    exemptions = Exemption.objects.filter(person=person).order_by('-date_from')
    clearances = DutyClearance.objects.filter(person=person).select_related('duty_type')

    context = {
        'person': person,
        'can_edit': access.can_edit_object(person),
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Карточка сотрудника',
        'title': f'Сотрудник: {person.last_name} {person.first_name}',
        'tab': tab,
        'exemptions': exemptions,
        'clearances': clearances,
    }

    return render(request, 'app/people/detail.html', context)


@login_required
def person_edit(request, pk):
    access = AccessService(request.user)
    person = get_object_or_404(Person, pk=pk)

    if not access.can_edit_object(person):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('people:person_list')

    if request.method == 'POST':
        form = PersonForm(request.POST, instance=person, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сотрудник обновлён')
            return redirect('people:person_detail', pk=person.pk)
    else:
        form = PersonForm(instance=person, user=request.user)

    return render(request, 'app/people/form.html', {
        'form': form,
        'person': person,
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Редактирование сотрудника',
        'title': f'Редактировать {person}',
    })


@login_required
def person_delete(request, pk):
    access = AccessService(request.user)
    person = get_object_or_404(Person, pk=pk)

    if not access.can_edit_object(person):
        messages.error(request, 'Нет прав для удаления')
        return redirect('people:person_list')

    if request.method == 'POST':
        person.delete()
        messages.success(request, 'Сотрудник удалён')
        return redirect('people:person_list')

    return render(request, 'app/people/delete.html', {
        'person': person,
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Удаление сотрудника',
        'title': 'Удаление сотрудника',
    })