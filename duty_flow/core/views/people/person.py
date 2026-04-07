from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from people.models import Person, Exemption, DutyClearance
from people.forms import PersonForm
from access_control.services import AccessManager


from access_control.services.labels import build_unit_path_label

def apply_person_access_to_form(form, access_manager, action: str):
    visible_fields = set(access_manager.visible_person_fields(action))
    editable_fields = set(access_manager.editable_person_fields(action))

    for field_name in list(form.fields.keys()):
        if field_name not in visible_fields:
            form.fields.pop(field_name, None)
            continue

        if field_name not in editable_fields:
            form.fields[field_name].disabled = True

    if "unit" in form.fields:
        if action == "create":
            units = access_manager.allowed_units_for_person_creation()
        elif action == "update":
            units = access_manager.allowed_units_for_person_update()
        else:
            units = None

        if units is not None:
            form.fields["unit"].queryset = units
            form.fields["unit"].label_from_instance = build_unit_path_label


@login_required
def person_list(request):
    access = AccessManager(request.user)
    people = access.scope_people(
        Person.objects.select_related("rank", "unit", "unit__unit_type").all()
    )

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
        'can_add': access.can_person("create"),
        'can_edit': True,
        'search_query': search_query,
    })


@login_required
def person_add(request):
    access = AccessManager(request.user)

    if not access.can_person("create"):
        messages.error(request, 'Нет прав для создания')
        return redirect('people:person_list')

    if request.method == 'POST':
        form = PersonForm(request.POST, user=request.user)
        apply_person_access_to_form(form, access, "create")

        if form.is_valid():
            person = form.save(commit=False)

            # Сохраняем старую рабочую бизнес-логику:
            # если form не даёт unit, подставляем подразделение текущего пользователя
            if getattr(person, "unit_id", None) is None:
                person.unit = request.user.profile.unit

            person.save()
            messages.success(request, f'Сотрудник {person} создан')
            return redirect('people:person_detail', pk=person.pk)
    else:
        form = PersonForm(user=request.user)
        apply_person_access_to_form(form, access, "create")

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
    access = AccessManager(request.user)
    person = get_object_or_404(
        Person.objects.select_related("rank", "unit", "unit__unit_type"),
        pk=pk
    )

    if not access.can_person("view", person):
        messages.error(request, 'Нет прав для просмотра')
        return redirect('people:person_list')

    tab = request.GET.get('tab', 'info')

    exemptions = Exemption.objects.filter(person=person).order_by('-date_from')
    clearances = DutyClearance.objects.filter(person=person).select_related('duty_type')

    context = {
        'person': person,
        'can_edit': access.can_person("update", person),
        'can_manage_exemptions': access.can_person("manage_exemptions", person),
        'can_manage_clearances': access.can_person("manage_clearances", person),
        'visible_fields': access.visible_person_fields("view"),
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
    access = AccessManager(request.user)
    person = get_object_or_404(Person, pk=pk)

    if not access.can_person("update", person):
        messages.error(request, 'Нет прав для редактирования')
        return redirect('people:person_detail', pk=person.pk)

    if request.method == 'POST':
        form = PersonForm(request.POST, instance=person, user=request.user)
        apply_person_access_to_form(form, access, "update")

        if form.is_valid():
            form.save()
            messages.success(request, 'Данные сотрудника обновлены')
            return redirect('people:person_detail', pk=person.pk)
    else:
        form = PersonForm(instance=person, user=request.user)
        apply_person_access_to_form(form, access, "update")

    return render(request, 'app/people/form.html', {
        'form': form,
        'person': person,
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Редактирование сотрудника',
        'title': f'Редактировать: {person.last_name} {person.first_name}',
    })


@login_required
def person_delete(request, pk):
    access = AccessManager(request.user)
    person = get_object_or_404(Person, pk=pk)

    if not access.can_person("delete", person):
        messages.error(request, 'Нет прав для удаления')
        return redirect('people:person_detail', pk=person.pk)

    if request.method == 'POST':
        person_name = str(person)
        person.delete()
        messages.success(request, f'Сотрудник {person_name} удалён')
        return redirect('people:person_list')

    return render(request, 'app/people/delete.html', {
        'person': person,
        'active_tab': 'people',
        'page_title': 'Сотрудники',
        'page_subtitle': 'Удаление сотрудника',
        'title': f'Удаление: {person.last_name} {person.first_name}',
    })