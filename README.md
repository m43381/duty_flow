units:
  Unit (id, name, parent → FK(Unit, null=True), unit_type → enum (academy, faculty, department, commandant))
  
people:
    Person (id, last_name, first_name, middle_name, rank → FK(Rank), unit → FK(Unit))
    Rank (id, name)
    Exemption (id, 
        person → FK(Person), 
        reason → enum (illness, leave, trip, other), 
        date_from, 
        date_to, 
        comment
    )
    DutyClearance (id, person → FK(Person), duty_type → FK(DutyType))
    DutyLoadStat (id, person → FK(Person), duty_count → IntegerField)

duties:
    DutyType (id, name, description - хз мб и не надо, можно еще количество людей добавить для универсальности)
    DutyAssignment (id, plan → FK(DutyPlan), person → FK(Person)) *хз мб это надо переместить в planning

planning:
    DutyPlan (
        id,
        date → DateField,
        unit → FK(Unit),
        duty_type → FK(DutyType),
    )
    PlanningEngine - сервис
