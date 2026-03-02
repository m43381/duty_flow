from django import template

register = template.Library()

@register.filter
def repeat(value, times):
    """
    Повторяет строку указанное количество раз.
    Использование в шаблоне: {{ '—'|repeat:level }}
    """
    try:
        times = int(times)
        return str(value) * max(0, times)
    except (ValueError, TypeError):
        return ''