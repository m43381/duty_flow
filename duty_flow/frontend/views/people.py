from core.crud import crud_views
from people.models import Person, Exemption, DutyClearance
from people.forms import PersonForm, ExemptionForm, DutyClearanceForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from users_app.access_service import AccessService

# Создаем CRUD для сотрудников (кроме detail, мы его переопределим)
person_views = crud_views(
    model=Person,
    form_class=PersonForm,
    template_prefix='person',
    list_url_name='person:person_list',
)

person_list = person_views['list']
person_add = person_views['create']
person_edit = person_views['update']
person_delete = person_views['delete']

@login_required
def person_detail(request, pk):
    """Детальный просмотр сотрудника с вкладками"""
    access = AccessService(request.user)
    person = get_object_or_404(Person, pk=pk)
    
    if not access.can_view_object(person):
        messages.error(request, 'Нет прав для просмотра')
        return redirect('person:person_list')
    
    # Получаем параметр tab из GET
    tab = request.GET.get('tab', 'info')
    
    context = {
        'person': person,
        'can_edit': access.can_edit_object(person),
        'active_tab': 'person',
        'title': f'Сотрудник: {person.last_name} {person.first_name}',
        'tab': tab,
    }
    
    # Добавляем данные для вкладок
    if tab == 'exemptions':
        context['exemptions'] = Exemption.objects.filter(person=person).order_by('-date_from')
    elif tab == 'clearances':
        context['clearances'] = DutyClearance.objects.filter(person=person).select_related('duty_type')
    
    return render(request, 'person/detail.html', context)