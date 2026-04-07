from django.db.models import QuerySet


def matches_scope(ctx, unit_id, scope: str) -> bool:
    if scope == "all":
        return True
    if not unit_id:
        return False
    if scope == "none":
        return False
    if scope == "own_unit":
        return unit_id == ctx.own_unit_id
    if scope == "descendants":
        return unit_id in ctx.descendant_unit_ids
    if scope == "own_and_descendants":
        return unit_id == ctx.own_unit_id or unit_id in ctx.descendant_unit_ids
    return False


def filter_queryset_by_scope(ctx, queryset: QuerySet, unit_lookup: str, scope: str) -> QuerySet:
    if scope == "all":
        return queryset
    if scope == "none":
        return queryset.none()

    if scope == "own_unit":
        if not ctx.own_unit_id:
            return queryset.none()
        return queryset.filter(**{unit_lookup: ctx.own_unit_id})

    if scope == "descendants":
        if not ctx.descendant_unit_ids:
            return queryset.none()
        return queryset.filter(**{f"{unit_lookup}__in": list(ctx.descendant_unit_ids)})

    if scope == "own_and_descendants":
        allowed_ids = set(ctx.descendant_unit_ids)
        if ctx.own_unit_id:
            allowed_ids.add(ctx.own_unit_id)
        if not allowed_ids:
            return queryset.none()
        return queryset.filter(**{f"{unit_lookup}__in": list(allowed_ids)})

    return queryset.none()