/**
 * FBReader Web - Reader JavaScript
 * Uses epub.js for rendering ePub books
 */

let book;
let rendition;
let currentLocation = null;
let settings = {
    theme: 'light',
    fontSize: 100,
    fontFamily: 'default',
    lineHeight: 1.6
};

// Load settings from localStorage
function loadSettings() {
    const saved = localStorage.getItem('readerSettings');
    if (saved) {
        try {
            settings = { ...settings, ...JSON.parse(saved) };
        } catch (e) {
            console.error('Failed to parse settings:', e);
        }
    }
}

function saveSettings() {
    localStorage.setItem('readerSettings', JSON.stringify(settings));
}

// Initialize reader
document.addEventListener('DOMContentLoaded', async () => {
    loadSettings();
    applyTheme(settings.theme);
    updateSettingsUI();
    setupEventListeners();

    try {
        await loadBook();
    } catch (error) {
        console.error('Failed to load book:', error);
        showError('Failed to load book. Please try again.');
    }
});

function setupEventListeners() {
    // Navigation buttons
    document.getElementById('prevBtn').addEventListener('click', () => {
        if (rendition) rendition.prev();
    });

    document.getElementById('nextBtn').addEventListener('click', () => {
        if (rendition) rendition.next();
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
            if (rendition) rendition.prev();
        } else if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
            if (rendition) rendition.next();
        } else if (e.key === 'Escape') {
            closeToc();
            closeSettings();
        }
    });

    // TOC button
    document.getElementById('tocBtn').addEventListener('click', toggleToc);

    // Settings button
    document.getElementById('settingsBtn').addEventListener('click', toggleSettings);

    // Fullscreen button
    document.getElementById('fullscreenBtn').addEventListener('click', toggleFullscreen);

    // Progress slider
    const progressSlider = document.getElementById('progressSlider');
    progressSlider.addEventListener('input', (e) => {
        const cfi = book.locations.cfiFromPercentage(e.target.value / 100);
        rendition.display(cfi);
    });

    // Theme buttons
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            applyTheme(btn.dataset.theme);
        });
    });

    // Click on viewer area to toggle UI
    document.getElementById('bookViewer').addEventListener('click', (e) => {
        // Only toggle if clicking on the viewer itself, not on buttons
        if (e.target === e.currentTarget || e.target.classList.contains('epub-container')) {
            toggleUI();
        }
    });

    // Touch support for swipe navigation
    let touchStartX = 0;
    const viewer = document.getElementById('bookViewer');

    viewer.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
    }, { passive: true });

    viewer.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].clientX;
        const diff = touchStartX - touchEndX;

        if (Math.abs(diff) > 50) {
            if (diff > 0) {
                if (rendition) rendition.next();
            } else {
                if (rendition) rendition.prev();
            }
        }
    }, { passive: true });
}

async function loadBook() {
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Fetch book content
    const response = await fetch(`/api/book/${bookId}/content`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const arrayBuffer = await response.arrayBuffer();

    // Initialize epub.js
    book = ePub(arrayBuffer);

    rendition = book.renderTo('bookViewer', {
        width: '100%',
        height: '100%',
        spread: 'none',
        flow: 'paginated'
    });

    // Apply initial settings
    applyReaderStyles();

    // Wait for book to be ready
    await book.ready;

    // Generate locations for progress tracking
    await book.locations.generate(1024);

    // Load TOC
    const navigation = await book.loaded.navigation;
    renderToc(navigation.toc);

    // Display book
    await rendition.display();

    // Hide loading overlay
    loadingOverlay.classList.add('hidden');

    // Listen for location changes
    rendition.on('relocated', (location) => {
        currentLocation = location;
        updateProgress(location);
        updateCurrentChapter(location);
        savePosition(location);
    });

    // Listen for rendered content to apply styles
    rendition.on('rendered', (section) => {
        applyReaderStyles();
    });
}

function renderToc(toc, parentElement = null, level = 0) {
    const container = parentElement || document.getElementById('tocList');

    if (!parentElement) {
        container.innerHTML = '';
    }

    toc.forEach(chapter => {
        const item = document.createElement('a');
        item.href = '#';
        item.className = `toc-item ${level > 0 ? `nested-${Math.min(level, 3)}` : ''}`;
        item.textContent = chapter.label;
        item.addEventListener('click', (e) => {
            e.preventDefault();
            rendition.display(chapter.href);
            closeToc();
        });
        container.appendChild(item);

        if (chapter.subitems && chapter.subitems.length > 0) {
            renderToc(chapter.subitems, container, level + 1);
        }
    });
}

function updateProgress(location) {
    if (!location || !book.locations) return;

    const progress = book.locations.percentageFromCfi(location.start.cfi);
    const percentage = Math.round(progress * 100);

    document.getElementById('progressSlider').value = percentage;
    document.getElementById('currentPage').textContent = `${percentage}%`;
}

function updateCurrentChapter(location) {
    if (!location) return;

    // Try to find current chapter from TOC
    const chapterDisplay = document.getElementById('currentChapter');

    book.loaded.navigation.then(nav => {
        const chapter = nav.toc.find(item => {
            return location.start.href && location.start.href.includes(item.href);
        });

        if (chapter) {
            chapterDisplay.textContent = chapter.label;
        } else {
            chapterDisplay.textContent = `Page ${location.start.displayed.page} of ${location.start.displayed.total}`;
        }
    });
}

async function savePosition(location) {
    if (!location) return;

    try {
        // Extract paragraph info from CFI 
        // This is a simplified version - FBReader uses a different position format
        const progress = book.locations.percentageFromCfi(location.start.cfi);
        const progressPercent = Math.round(progress * 100);
        const paragraph = Math.round(progress * 10000); // Approximate

        await fetch(`/api/book/${bookId}/position`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paragraph: paragraph,
                word: 0,
                char: 0,
                progress: progressPercent
            })
        });
    } catch (error) {
        console.error('Failed to save position:', error);
    }
}

function applyTheme(theme) {
    settings.theme = theme;
    saveSettings();

    const page = document.body;
    page.classList.remove('theme-light', 'theme-sepia', 'theme-dark');
    page.classList.add(`theme-${theme}`);

    // Update active button
    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === theme);
    });

    // Apply to epub content
    if (rendition) {
        let bgColor, textColor;
        switch (theme) {
            case 'sepia':
                bgColor = '#f4ecd8';
                textColor = '#5b4636';
                break;
            case 'dark':
                bgColor = '#1a1a1a';
                textColor = '#e0e0e0';
                break;
            default: // light
                bgColor = '#ffffff';
                textColor = '#1a1a1a';
        }

        rendition.themes.override('color', textColor);
        rendition.themes.override('background', bgColor);
    }
}

function applyReaderStyles() {
    if (!rendition) return;

    const fontFamily = settings.fontFamily === 'default' ? '' : settings.fontFamily;

    rendition.themes.default({
        body: {
            'font-size': `${settings.fontSize}% !important`,
            'line-height': `${settings.lineHeight} !important`,
            'font-family': fontFamily ? `${fontFamily} !important` : 'inherit'
        }
    });
}

function changeFontSize(delta) {
    settings.fontSize = Math.max(60, Math.min(200, settings.fontSize + delta));
    document.getElementById('fontSizeDisplay').textContent = `${settings.fontSize}%`;
    saveSettings();
    applyReaderStyles();
}

function changeFontFamily(family) {
    settings.fontFamily = family;
    saveSettings();
    applyReaderStyles();
}

function changeLineHeight(value) {
    settings.lineHeight = parseFloat(value);
    saveSettings();
    applyReaderStyles();
}

function updateSettingsUI() {
    document.getElementById('fontSizeDisplay').textContent = `${settings.fontSize}%`;
    document.getElementById('fontFamily').value = settings.fontFamily;
    document.getElementById('lineHeight').value = settings.lineHeight;

    document.querySelectorAll('.theme-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === settings.theme);
    });
}

function toggleToc() {
    const sidebar = document.getElementById('tocSidebar');
    sidebar.classList.toggle('open');
    closeSettings();
}

function closeToc() {
    document.getElementById('tocSidebar').classList.remove('open');
}

function toggleSettings() {
    const panel = document.getElementById('settingsPanel');
    panel.classList.toggle('open');
    closeToc();
}

function closeSettings() {
    document.getElementById('settingsPanel').classList.remove('open');
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error('Fullscreen error:', err);
        });
    } else {
        document.exitFullscreen();
    }
}

function toggleUI() {
    const header = document.getElementById('readerHeader');
    const footer = document.getElementById('readerFooter');

    header.classList.toggle('hidden');
    footer.classList.toggle('hidden');
}

function showError(message) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.innerHTML = `
        <p style="color: var(--error);">${message}</p>
        <a href="/library" class="btn-primary" style="margin-top: var(--space-4); display: inline-block; padding: var(--space-3) var(--space-6); text-decoration: none;">
            Back to Library
        </a>
    `;
}
