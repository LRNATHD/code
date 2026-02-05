/**
 * FBReader Web - Library JavaScript
 */

let allBooks = [];
let currentFilter = 'all';
let currentView = 'grid';
let searchQuery = '';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadBooks();
    setupEventListeners();
});

function setupEventListeners() {
    // Search
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', debounce((e) => {
        searchQuery = e.target.value.toLowerCase();
        renderBooks();
    }, 300));

    // View toggle
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentView = btn.dataset.view;

            const container = document.getElementById('booksContainer');
            container.classList.remove('grid-view', 'list-view');
            container.classList.add(`${currentView}-view`);
        });
    });

    // Filter navigation
    document.querySelectorAll('.nav-item[data-filter]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.nav-item[data-filter]').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            currentFilter = item.dataset.filter;
            renderBooks();
        });
    });

    // Close modal on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

async function loadBooks() {
    const container = document.getElementById('booksContainer');
    container.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>Loading your library...</p>
        </div>
    `;

    try {
        const response = await fetch('/api/books');
        if (!response.ok) {
            throw new Error('Failed to fetch books');
        }

        const data = await response.json();
        allBooks = data.books;
        renderBooks();

        document.querySelector('.book-count').textContent = `${data.count} books in your library`;
    } catch (error) {
        console.error('Error loading books:', error);
        container.innerHTML = `
            <div class="loading-state">
                <p style="color: var(--error);">Failed to load library. Please try again.</p>
                <button onclick="loadBooks()" class="btn-primary" style="margin-top: var(--space-4); width: auto; padding: var(--space-3) var(--space-6);">
                    Retry
                </button>
            </div>
        `;
    }
}

function renderBooks() {
    const container = document.getElementById('booksContainer');

    // Filter books
    let filtered = allBooks.filter(book => {
        // Search filter
        if (searchQuery) {
            const searchable = `${book.title} ${book.authors.join(' ')} ${book.series || ''}`.toLowerCase();
            if (!searchable.includes(searchQuery)) {
                return false;
            }
        }

        // Category filter
        if (currentFilter === 'reading') {
            return book.progress > 0 && book.progress < 100;
        } else if (currentFilter === 'completed') {
            return book.progress >= 100;
        }

        return true;
    });

    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="loading-state">
                <p>No books found${searchQuery ? ' matching your search' : ''}.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(book => `
        <article class="book-card" onclick="showBookDetail(${book.book_id})" data-book-id="${book.book_id}">
            <div class="book-cover">
                <img src="/api/book/${book.book_id}/cover" alt="${escapeHtml(book.title)}" loading="lazy" 
                     onerror="this.src='/static/img/no-cover.svg'">
                ${book.progress > 0 ? `
                <div class="progress-indicator">
                    <div class="progress-bar" style="width: ${book.progress}%"></div>
                </div>
                ` : ''}
            </div>
            <div class="book-info">
                <h3>${escapeHtml(book.title)}</h3>
                <p class="author">${escapeHtml(book.authors.join(', ') || 'Unknown Author')}</p>
            </div>
        </article>
    `).join('');
}

function showBookDetail(bookId) {
    const book = allBooks.find(b => b.book_id === bookId);
    if (!book) return;

    const modal = document.getElementById('bookModal');
    const modalBody = document.getElementById('modalBody');

    // Strip HTML from annotation for display
    let annotation = book.annotation || '';
    if (annotation) {
        const temp = document.createElement('div');
        temp.innerHTML = annotation;
        annotation = temp.textContent || temp.innerText || '';
    }

    modalBody.innerHTML = `
        <div class="modal-book">
            <div class="modal-cover">
                <img src="/api/book/${book.book_id}/cover" alt="${escapeHtml(book.title)}"
                     onerror="this.src='/static/img/no-cover.svg'">
            </div>
            <div class="modal-details">
                <h2>${escapeHtml(book.title)}</h2>
                <p class="author">${escapeHtml(book.authors.join(', ') || 'Unknown Author')}</p>
                
                <div class="meta">
                    ${book.series ? `<span>Series: ${escapeHtml(book.series)}${book.series_index ? ` #${book.series_index}` : ''}</span>` : ''}
                    <span>Language: ${book.language.toUpperCase()}</span>
                    ${book.progress > 0 ? `<span>Progress: ${Math.round(book.progress)}%</span>` : ''}
                </div>
                
                ${annotation ? `<div class="annotation">${escapeHtml(annotation)}</div>` : ''}
                
                <div class="modal-actions">
                    <a href="/read/${book.book_id}" class="btn-read">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                        </svg>
                        <span>${book.progress > 0 ? 'Continue Reading' : 'Start Reading'}</span>
                    </a>
                </div>
            </div>
        </div>
    `;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('bookModal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
