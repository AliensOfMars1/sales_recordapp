// Dark/Light mode toggle functionality

// Get the theme toggle button (will be added to the navbar)
let themeToggleBtn = null;

// Check for saved user preference, otherwise use system preference
function getInitialTheme() {
    const savedTheme = localStorage.getItem('barberTheme');
    if (savedTheme) {
        return savedTheme;
    }
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}

// Apply theme to body
function applyTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
        document.body.classList.remove('light-mode');
    } else {
        document.body.classList.add('light-mode');
        document.body.classList.remove('dark-mode');
    }
    localStorage.setItem('barberTheme', theme);
    
    // Update button icon if it exists
    if (themeToggleBtn) {
        const icon = themeToggleBtn.querySelector('i');
        if (icon) {
            if (theme === 'dark') {
                icon.className = 'fas fa-sun';
                themeToggleBtn.title = 'Switch to Light Mode';
            } else {
                icon.className = 'fas fa-moon';
                themeToggleBtn.title = 'Switch to Dark Mode';
            }
        }
    }
}

// Toggle between dark and light mode
function toggleTheme() {
    const currentTheme = localStorage.getItem('barberTheme') || getInitialTheme();
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

// Initialize theme toggle button
function initThemeToggle(buttonId = 'themeToggleBtn') {
    themeToggleBtn = document.getElementById(buttonId);
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
        const savedTheme = localStorage.getItem('barberTheme') || getInitialTheme();
        const icon = themeToggleBtn.querySelector('i');
        if (icon) {
            if (savedTheme === 'dark') {
                icon.className = 'fas fa-sun';
                themeToggleBtn.title = 'Switch to Light Mode';
            } else {
                icon.className = 'fas fa-moon';
                themeToggleBtn.title = 'Switch to Dark Mode';
            }
        }
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Apply saved theme
    const savedTheme = localStorage.getItem('barberTheme') || getInitialTheme();
    applyTheme(savedTheme);
    
    // Initialize toggle button
    initThemeToggle();
});