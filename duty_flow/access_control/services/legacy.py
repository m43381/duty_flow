from units.models import Unit


class LegacyAccessAdapter:
    def __init__(self, user):
        self.user = user

    def service(self):
        from users_app.access_service import AccessService
        return AccessService(self.user)

    # ---------- users ----------
    def can_user(self, action, target_user=None):
        access = self.service()

        if action == "view":
            if target_user is None:
                return True
            return access.can_view_user(target_user)

        if action == "create":
            return access.can_create_user()

        if action == "update" and target_user is not None:
            return access.can_edit_user(target_user)

        if action == "delete" and target_user is not None:
            return access.can_delete_user(target_user)

        if action == "change_password" and target_user is not None:
            return access.can_change_password(target_user)

        return False

    def visible_users(self):
        return self.service().get_visible_users()

    def available_creation_units(self):
        access = self.service()
        available_units = [access.user_unit]
        available_units.extend(list(access.user_unit.children.all()))
        return Unit.objects.filter(id__in=[unit.id for unit in available_units]).order_by("name")

    # ---------- people ----------
    def can_person(self, action, person=None):
        access = self.service()

        if action == "view":
            if person is None:
                return True
            return access.can_view_object(person)

        if action == "create":
            return access.can_create_in_unit(access.user_unit)

        if action in {"update", "manage_exemptions", "manage_clearances"} and person is not None:
            return access.can_edit_object(person)

        if action == "delete" and person is not None:
            return access.can_edit_object(person)

        return False

    def visible_people(self, queryset):
        return self.service().get_visible_queryset(queryset)