from units.models import Unit


def get_scope_unit_ids(ctx, scope: str) -> set[int]:
    if scope == "all":
        return set(Unit.objects.values_list("id", flat=True))

    if scope == "none":
        return set()

    if scope == "own_unit":
        return {ctx.own_unit_id} if ctx.own_unit_id else set()

    if scope == "descendants":
        return set(ctx.descendant_unit_ids)

    if scope == "own_and_descendants":
        result = set(ctx.descendant_unit_ids)
        if ctx.own_unit_id:
            result.add(ctx.own_unit_id)
        return result

    return set()