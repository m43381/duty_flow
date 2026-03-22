class ScheduleTable {
    constructor(container) {
        this.container = container;
        this.init();
    }
    
    init() {
        this.bindEvents();
    }
    
    bindEvents() {
        // Обработка кнопок "Снять"
        this.container.querySelectorAll('.assignment-remove').forEach(btn => {
            btn.addEventListener('click', (e) => this.removeAssignment(e));
        });
        
        // Обработка select'ов
        this.container.querySelectorAll('.schedule-select').forEach(select => {
            select.addEventListener('change', (e) => this.onSelectChange(e));
        });
    }
    
    removeAssignment(event) {
        const button = event.currentTarget;
        const cell = button.closest('td');
        const date = button.dataset.date;
        const dutyTypeId = button.dataset.duty;
        const form = button.closest('form');
        
        // Создаем скрытый input с пустым значением
        const inputName = `day_${date}_${dutyTypeId}`;
        
        // Удаляем существующий input если есть
        const existingInput = form.querySelector(`input[name="${inputName}"]`);
        if (existingInput) existingInput.remove();
        
        // Создаем новый input с пустым значением
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = inputName;
        input.value = '';  // Пустое значение!
        form.appendChild(input);
        
        // Визуально очищаем ячейку
        this.clearCell(cell, date, dutyTypeId);
        
        // Добавляем лог для отладки
        console.log(`Снято назначение: ${inputName} = ""`);
    }
    
    clearCell(cell, date, dutyTypeId) {
        cell.classList.remove('schedule-cell--assigned');
        cell.classList.add('schedule-cell--empty');
        
        // Получаем options из существующего select
        const existingSelect = this.container.querySelector('.schedule-select');
        let optionsHtml = '';
        if (existingSelect) {
            optionsHtml = existingSelect.innerHTML;
        } else {
            optionsHtml = '<option value="">— Выбрать —</option>';
            // Добавляем options из available_units (нужно передать в data-атрибут)
            const unitsData = this.container.dataset.units;
            if (unitsData) {
                const units = JSON.parse(unitsData);
                units.forEach(unit => {
                    optionsHtml += `<option value="${unit.id}">${unit.name}</option>`;
                });
            }
        }
        
        cell.innerHTML = `
            <select name="day_${date}_${dutyTypeId}" class="schedule-select">
                ${optionsHtml}
            </select>
        `;
        
        // Привязываем события к новому select
        const newSelect = cell.querySelector('.schedule-select');
        if (newSelect) {
            newSelect.addEventListener('change', (e) => this.onSelectChange(e));
        }
    }
    
    onSelectChange(event) {
        const select = event.currentTarget;
        select.classList.add('changed');
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.schedule-table-container');
    if (container) {
        window.scheduleTable = new ScheduleTable(container);
    }
});