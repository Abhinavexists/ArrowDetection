// Theme Management
function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDark ? 'dark' : 'light');
    }
}

// View Toggle
document.querySelector('.view-toggle button').addEventListener('click', function() {
    const streamsGrid = document.querySelector('.streams-grid');
    const isSingleView = streamsGrid.classList.contains('single-view');
    
    if (isSingleView) {
        streamsGrid.classList.remove('single-view');
        this.textContent = 'Single View';
    } else {
        streamsGrid.classList.add('single-view');
        this.textContent = 'Split View';
    }
});

// Collapsible Sections
function expandAll() {
    document.querySelectorAll('.collapsible').forEach(collapsible => {
        collapsible.classList.add('active');
    });
}

function collapseAll() {
    document.querySelectorAll('.collapsible').forEach(collapsible => {
        collapsible.classList.remove('active');
    });
}

document.querySelectorAll('.collapsible-header').forEach(header => {
    header.addEventListener('click', function() {
        const collapsible = this.parentElement;
        collapsible.classList.toggle('active');
    });
});

// Color Presets
const presets = {
    red: { l_h: 0, l_s: 100, l_v: 100, u_h: 10, u_s: 255, u_v: 255 },
    blue: { l_h: 100, l_s: 100, l_v: 100, u_h: 130, u_s: 255, u_v: 255 },
    green: { l_h: 40, l_s: 100, l_v: 100, u_h: 80, u_s: 255, u_v: 255 },
    yellow: { l_h: 20, l_s: 100, l_v: 100, u_h: 40, u_s: 255, u_v: 255 }
};

function applyPreset(color) {
    const preset = presets[color];
    if (!preset) return;

    // Update all HSV sliders
    Object.keys(preset).forEach(key => {
        const slider = document.querySelector(`input[name="${key}"]`);
        if (slider) {
            slider.value = preset[key];
            slider.dispatchEvent(new Event('input'));
        }
    });

    // Update active state of preset buttons
    document.querySelectorAll('.preset').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase() === color) {
            btn.classList.add('active');
        }
    });
}

// HSV Sliders
document.querySelectorAll('.slider').forEach(slider => {
    slider.addEventListener('input', function() {
        const valueDisplay = this.parentElement.querySelector('.slider-value');
        if (valueDisplay) {
            valueDisplay.textContent = this.value;
        }
    });
});

function resetHSV() {
    document.querySelectorAll('.slider').forEach(slider => {
        slider.value = slider.defaultValue;
        slider.dispatchEvent(new Event('input'));
    });
}

// Socket.IO Connection
const socket = io();

socket.on('connect', () => {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status-text');
    if (statusIndicator && statusText) {
        statusIndicator.classList.add('connected');
        statusText.textContent = 'Connected';
    }
});

socket.on('disconnect', () => {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status-text');
    if (statusIndicator && statusText) {
        statusIndicator.classList.remove('connected');
        statusText.textContent = 'Disconnected';
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    resetHSV();
}); 