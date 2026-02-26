from django.contrib import admin
from .models import Rank

@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)
    list_editable = ('order',)