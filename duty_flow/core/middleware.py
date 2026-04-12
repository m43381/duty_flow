from django.contrib import messages
from django.shortcuts import redirect

from access_control.services import AccessManager, get_effective_level, get_menu_key_by_namespace, get_menu_visibility_for_level


class MenuAccessMiddleware:
    """
    Блокирует доступ к разделам, если пункт меню для текущего уровня скрыт.
    Работает по namespace маршрута.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None

        resolver_match = getattr(request, "resolver_match", None)
        if not resolver_match:
            return None

        namespace = resolver_match.namespace
        if not namespace:
            return None

        menu_key = get_menu_key_by_namespace(namespace)
        if not menu_key:
            return None

        access = AccessManager(request.user)
        ruleset = access.ruleset
        level = get_effective_level(request.user)

        is_visible = get_menu_visibility_for_level(ruleset, menu_key, level)

        if menu_key == "access_control" and level == 0:
            return None

        if not is_visible:
            messages.error(request, "У вас нет доступа к этому разделу")
            return redirect("auth:dashboard")

        return None