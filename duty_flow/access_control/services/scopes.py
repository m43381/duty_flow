from units.models import Unit


def _child_ids(ctx):
    return set(Unit.objects.filter(parent_id=ctx.own_unit_id).values_list("id", flat=True))


def _all_descendant_ids(ctx):
    return set(ctx.descendant_unit_ids)


def allowed_unit_ids_by_scope(ctx, scope: str) -> set[int]:
    own_id = ctx.own_unit_id
    child_ids = _child_ids(ctx)
    all_desc_ids = _all_descendant_ids(ctx)

    if scope == "none":
        return set()

    if scope == "own_unit":
        return {own_id} if own_id else set()

    if scope == "children":
        return child_ids

    if scope == "own_and_children":
        ids = set(child_ids)
        if own_id:
            ids.add(own_id)
        return ids

    if scope == "all_descendants":
        return all_desc_ids

    if scope == "own_and_all_descendants":
        ids = set(all_desc_ids)
        if own_id:
            ids.add(own_id)
        return ids

    if scope == "all":
        return set(Unit.objects.values_list("id", flat=True))

    return set()


def matches_scope(ctx, unit_id, scope: str) -> bool:
    if unit_id is None:
        return False
    return unit_id in allowed_unit_ids_by_scope(ctx, scope)


def filter_queryset_by_scope(ctx, queryset, lookup: str, scope: str):
    ids = allowed_unit_ids_by_scope(ctx, scope)

    if scope == "all":
        return queryset

    if not ids:
        return queryset.none()

    return queryset.filter(**{f"{lookup}__in": list(ids)})