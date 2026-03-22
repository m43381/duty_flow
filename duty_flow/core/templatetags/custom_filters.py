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
    
@register.filter
def get_item(dictionary, key):
    """Получает элемент из словаря по ключу"""
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        try:
            return dictionary[key]
        except (KeyError, TypeError):
            return None