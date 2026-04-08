def build_duty_type_label(duty_type):
    parts = [duty_type.name]

    if getattr(duty_type, "unit", None):
        parts.append(f"подразделение: {duty_type.unit.name}")
    elif getattr(duty_type, "created_by_unit", None):
        parts.append(f"создано: {duty_type.created_by_unit.name}")

    return " — ".join(parts)