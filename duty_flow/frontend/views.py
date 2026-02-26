from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

def index(request):
    """Главная страница"""
    return render(request, 'index.html')

@login_required
def dashboard(request):
    """Общий дашборд (перенаправляет в зависимости от роли)"""
    profile = request.user.profile
    
    # Контекст с данными (позже заменим на реальные запросы к БД)
    context = {
        'page_title': f'Дашборд - {profile.unit.name}',
        'active_tab': 'dashboard',
        'total_people': 150,  # Заглушка
        'today_plans': 12,     # Заглушка
        'active_exemptions': 5, # Заглушка
        'total_assignments': 450, # Заглушка
        'upcoming_plans': [],   # Заглушка
    }
    
    return render(request, 'cabinets/dashboard.html', context)

@login_required
def commandant_cabinet(request):
    """Кабинет коменданта"""
    return render(request, 'cabinets/commandant.html', {
        'page_title': 'Кабинет коменданта',
        'active_tab': 'dashboard'
    })

@login_required
def faculty_cabinet(request):
    """Кабинет факультета"""
    return render(request, 'cabinets/faculty.html', {
        'page_title': 'Кабинет факультета',
        'active_tab': 'dashboard'
    })

@login_required
def department_cabinet(request):
    """Кабинет кафедры"""
    return render(request, 'cabinets/department.html', {
        'page_title': 'Кабинет кафедры',
        'active_tab': 'dashboard'
    })