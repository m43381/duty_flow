// static/js/components/assignment-modal.js
// Модальное окно для назначения сотрудников

class AssignmentModal {
    constructor() {
        this.modal = null;
        this.currentPlanId = null;
        this.currentUrl = window.location.href;
        this.csrfToken = this.getCsrfToken();
        
        this.init();
    }
    
    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        return cookieValue ? cookieValue.split('=')[1] : '';
    }
    
    init() {
        // Создаем модальное окно, если его нет
        if (!document.getElementById('assignmentModal')) {
            this.createModal();
        }
        this.modal = document.getElementById('assignmentModal');
        
        // Закрытие по клику на фон
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }
    
    createModal() {
        const modalHtml = `
            <div id="assignmentModal" class="assignment-modal" style="display: none;">
                <div class="assignment-modal__content">
                    <div class="assignment-modal__header">
                        <h3 class="assignment-modal__title">Назначение сотрудников</h3>
                        <span class="assignment-modal__close" onclick="window.assignmentModal.close()">&times;</span>
                    </div>
                    <div class="assignment-modal__body">
                        <div class="assignment-modal__info">
                            <div class="assignment-modal__info-row">
                                <span class="assignment-modal__info-label">Тип наряда:</span>
                                <span class="assignment-modal__info-value" id="modalDuty"></span>
                            </div>
                            <div class="assignment-modal__info-row">
                                <span class="assignment-modal__info-label">Подразделение:</span>
                                <span class="assignment-modal__info-value" id="modalUnit"></span>
                            </div>
                            <div class="assignment-modal__info-row">
                                <span class="assignment-modal__info-label">Требуется:</span>
                                <span class="assignment-modal__info-value" id="modalRequired"></span>
                                <span>чел.</span>
                                <span class="assignment-modal__info-label" style="margin-left: 1rem;">Назначено:</span>
                                <span class="assignment-modal__info-value" id="modalCurrentCount"></span>
                                <span>чел.</span>
                            </div>
                        </div>
                        
                        <div class="assignment-modal__section">
                            <h4 class="assignment-modal__section-title">Назначенные сотрудники</h4>
                            <div id="assignedPeople" class="assignment-modal__people-list"></div>
                        </div>
                        
                        <div class="assignment-modal__section">
                            <h4 class="assignment-modal__section-title">Доступные сотрудники</h4>
                            <div id="availablePeople" class="assignment-modal__people-list"></div>
                        </div>
                        
                        <div class="assignment-modal__section">
                            <h4 class="assignment-modal__section-title">Недоступные сотрудники</h4>
                            <div id="unavailablePeople" class="assignment-modal__people-list"></div>
                        </div>
                    </div>
                    <div class="assignment-modal__footer">
                        <button class="btn btn-secondary" onclick="window.assignmentModal.close()">Закрыть</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
    
    open(planId, dutyName, unitName) {
        if (!planId) return;
        
        this.currentPlanId = planId;
        document.getElementById('modalDuty').textContent = dutyName;
        document.getElementById('modalUnit').textContent = unitName;
        
        this.loadPeople(planId);
        this.modal.style.display = 'flex';
    }
    
    close() {
        this.modal.style.display = 'none';
        this.currentPlanId = null;
    }
    
    loadPeople(planId) {
        fetch(`/assignments/get-people/${planId}/`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('modalRequired').textContent = data.required_people;
                document.getElementById('modalCurrentCount').textContent = data.current_count;
                this.renderAssignedPeople(data.assigned);
                this.renderAvailablePeople(data.available);
                this.renderUnavailablePeople(data.unavailable);
            })
            .catch(error => {
                console.error('Error loading people:', error);
            });
    }
    
    renderAvailablePeople(people) {
        const container = document.getElementById('availablePeople');
        if (!people || people.length === 0) {
            container.innerHTML = '<div class="assignment-modal__empty">Нет доступных сотрудников</div>';
            return;
        }
        
        container.innerHTML = people.map(p => `
            <div class="assignment-modal__person-item">
                <div class="assignment-modal__person-info">
                    <span class="assignment-modal__person-name">${this.escapeHtml(p.name)}</span>
                    <span class="assignment-modal__person-rank">${this.escapeHtml(p.rank)}</span>
                </div>
                <form method="post" action="/assignments/assign/${this.currentPlanId}/" style="margin: 0;">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${this.csrfToken}">
                    <input type="hidden" name="person_id" value="${p.id}">
                    <input type="hidden" name="next" value="${this.currentUrl}">
                    <button type="submit" class="btn btn-primary assignment-modal__btn-sm">➕ Назначить</button>
                </form>
            </div>
        `).join('');
    }
    
    renderAssignedPeople(people) {
        const container = document.getElementById('assignedPeople');
        if (!people || people.length === 0) {
            container.innerHTML = '<div class="assignment-modal__empty">Нет назначенных сотрудников</div>';
            return;
        }
        
        container.innerHTML = people.map(p => `
            <div class="assignment-modal__person-item">
                <div class="assignment-modal__person-info">
                    <span class="assignment-modal__person-name">${this.escapeHtml(p.name)}</span>
                    <span class="assignment-modal__person-rank">${this.escapeHtml(p.rank)}</span>
                </div>
                <form method="post" action="/assignments/unassign/${p.id}/" style="margin: 0;">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${this.csrfToken}">
                    <input type="hidden" name="next" value="${this.currentUrl}">
                    <button type="submit" class="btn assignment-modal__btn-sm assignment-modal__btn-danger">🗑️ Удалить</button>
                </form>
            </div>
        `).join('');
    }
    
    renderUnavailablePeople(people) {
        const container = document.getElementById('unavailablePeople');
        if (!people || people.length === 0) {
            container.innerHTML = '<div class="assignment-modal__empty">Нет недоступных сотрудников</div>';
            return;
        }
        
        container.innerHTML = people.map(p => `
            <div class="assignment-modal__person-item">
                <div class="assignment-modal__person-info">
                    <span class="assignment-modal__person-name">${this.escapeHtml(p.name)}</span>
                    <span class="assignment-modal__person-rank">${this.escapeHtml(p.rank)}</span>
                    <span class="assignment-modal__person-reason">(${this.escapeHtml(p.reason)})</span>
                </div>
            </div>
        `).join('');
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Глобальный экземпляр
window.assignmentModal = new AssignmentModal();

// Функция для открытия модального окна (для вызова из onclick)
function openAssignmentModal(planId, dutyName, unitName) {
    window.assignmentModal.open(planId, dutyName, unitName);
}

function closeAssignmentModal() {
    window.assignmentModal.close();
}