document.addEventListener('DOMContentLoaded', function() {
    console.log('Theme.js loaded');
    
    const lightTheme = document.getElementById('theme-light');
    const darkTheme = document.getElementById('theme-dark');
    const themeBtn = document.getElementById('themeBtn');
    
    if (!lightTheme || !darkTheme) {
        console.error('Theme CSS files not found!');
        return;
    }
    
    // Функция установки темы
    window.setTheme = function(theme) {
        console.log('Setting theme to:', theme);
        
        if (theme === 'dark') {
            lightTheme.disabled = true;
            darkTheme.disabled = false;
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('dutyflow-theme', 'dark');
        } else {
            lightTheme.disabled = false;
            darkTheme.disabled = true;
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('dutyflow-theme', 'light');
        }
    };
    
    // Функция переключения темы
    window.toggleTheme = function() {
        const isDark = lightTheme.disabled === true;
        window.setTheme(isDark ? 'light' : 'dark');
    };
    
    // Загружаем сохраненную тему
    const savedTheme = localStorage.getItem('dutyflow-theme') || 'light';
    window.setTheme(savedTheme);
    
    // Обработчик кнопки
    if (themeBtn) {
        themeBtn.addEventListener('click', window.toggleTheme);
    }
    
    console.log('Theme manager ready');
});