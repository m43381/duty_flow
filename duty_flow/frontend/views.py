from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def commandant(request):
    return render(request, 'cabinets/commandant.html')

def faculty(request):
    return render(request, 'cabinets/faculty.html')

def department(request):
    return render(request, 'cabinets/department.html')