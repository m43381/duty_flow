def build_unit_path_label(unit):
    """
    Возвращает подпись подразделения с цепочкой родителей:
    Академия / Факультет / Кафедра
    """
    parts = []
    current = unit

    while current is not None:
        parts.append(current.name)
        current = getattr(current, "parent", None)

    parts.reverse()
    return " / ".join(parts)