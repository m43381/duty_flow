from access_control.services import build_navigation_sections


def navigation_context(request):
    if not request.user.is_authenticated:
        return {}

    return {
        "nav_sections": build_navigation_sections(request.user)
    }