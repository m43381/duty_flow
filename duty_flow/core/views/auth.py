from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect

def index(request):
    """Главная страница"""
    return render(request, 'public/index.html')


def logout_view(request):
    logout(request)
    return redirect('auth:index')


@login_required
def dashboard(request):
    """Дашборд"""
    profile = request.user.profile
    context = {
        'page_title': f'Дашборд - {profile.unit.name}',
        'active_tab': 'dashboard',
        'total_people': 0,
        'today_plans': 0,
        'active_exemptions': 0,
        'total_assignments': 0,
        'upcoming_plans': [],
    }
    return render(request, 'app/dashboard.html', context)

# Заглушки для всех разделов
@login_required
def person_list(request):
    return render(request, 'cabinets/person_list.html', {
        'page_title': 'Сотрудники',
        'active_tab': 'people'
    })

@login_required
def duty_plan_list(request):
    return render(request, 'cabinets/plan_list.html', {
        'page_title': 'Планы нарядов',
        'active_tab': 'plans'
    })

@login_required
def duty_type_list(request):
    # Проверка доступа
    if request.user.profile.access_level not in ['academy', 'faculty']:
        return render(request, 'cabinets/access_denied.html', {
            'page_title': 'Доступ запрещен'
        })
    return render(request, 'cabinets/type_list.html', {
        'page_title': 'Типы нарядов',
        'active_tab': 'types'
    })

@login_required
def unit_list(request):
    return render(request, 'cabinets/unit_list.html', {
        'page_title': 'Подразделения',
        'active_tab': 'units'
    })

@login_required
def user_list(request):
    return render(request, 'cabinets/user_list.html', {
        'page_title': 'Пользователи',
        'active_tab': 'users'
    })
