// Enhanced Dark Mode toggling for PantryCheff
document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('dark-mode-toggle');
    const html = document.getElementById('html-root');
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');

    // Function to update icons based on current theme
    function updateIcons(isDark) {
        if (isDark) {
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
        } else {
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
        }
    }

    // Function to apply theme and update UI
    function applyTheme() {
        const theme = localStorage.getItem('pantrycheff-theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (theme === 'dark' || (!theme && prefersDark)) {
            enableDarkMode();
        } else {
            disableDarkMode();
        }
    }

    // Enhanced dark mode function
    function enableDarkMode() {
        html.classList.add('dark');
        localStorage.setItem('pantrycheff-theme', 'dark');
        updateIcons(true);
        updateThemeColor(true);
        
        // Add smooth transition class
        html.classList.add('theme-transition');
    }

    // Enhanced light mode function
    function disableDarkMode() {
        html.classList.remove('dark');
        localStorage.setItem('pantrycheff-theme', 'light');
        updateIcons(false);
        updateThemeColor(false);
        
        // Add smooth transition class
        html.classList.add('theme-transition');
    }

    // Function to update mobile browser theme color
    function updateThemeColor(isDark) {
        let themeColorMeta = document.querySelector('meta[name="theme-color"]');
        if (!themeColorMeta) {
            themeColorMeta = document.createElement('meta');
            themeColorMeta.name = 'theme-color';
            document.head.appendChild(themeColorMeta);
        }
        themeColorMeta.content = isDark ? '#0f172a' : '#10b981'; // dark: slate-900, light: primary
    }

    // Toggle button click handler
    if (toggleButton) {
        toggleButton.addEventListener('click', () => {
            const isDark = html.classList.contains('dark');
            if (isDark) {
                disableDarkMode();
            } else {
                enableDarkMode();
            }
        });
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('pantrycheff-theme')) {
            if (e.matches) {
                enableDarkMode();
            } else {
                disableDarkMode();
            }
        }
    });

    // Initialize theme on load
    applyTheme();
});