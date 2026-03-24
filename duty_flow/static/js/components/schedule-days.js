document.addEventListener('DOMContentLoaded', function() {
    const selects = document.querySelectorAll('.schedule-select');
    
    selects.forEach(select => {
        const originalValue = select.dataset.originalValue;
        
        if (select.value !== originalValue) {
            select.classList.add('changed');
        }
        
        select.addEventListener('change', function() {
            if (this.value !== this.dataset.originalValue) {
                this.classList.add('changed');
            } else {
                this.classList.remove('changed');
            }
        });
    });
    
    const saveBtn = document.getElementById('saveBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            this.textContent = '💾 Сохранение...';
            this.disabled = true;
            setTimeout(() => {
                this.textContent = '💾 Сохранить изменения';
                this.disabled = false;
            }, 1000);
        });
    }
});