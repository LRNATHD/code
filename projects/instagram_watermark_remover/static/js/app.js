/**
 * Instagram Watermark Remover - Frontend Application
 * Handles UI interactions, API calls, and state management
 */

class WatermarkRemoverApp {
    constructor() {
        this.state = {
            currentSource: 'google',
            currentView: 'source',
            selectedPosition: 'auto',
            selectedPhotos: new Set(),
            photos: [],
            processedPhotos: [],
            albums: [],
            isLoading: false,
            isProcessing: false,
        };

        this.init();
    }

    init() {
        this.bindEvents();
        this.checkStatus();
        this.loadLocalPhotos();
        this.loadProcessedPhotos();
        this.fetchAlbums();
    }

    // ========================================
    // Event Binding
    // ========================================

    bindEvents() {
        // Source tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchSource(e.target.dataset.source));
        });

        // Photo view tabs
        document.querySelectorAll('.photo-tab').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchView(e.target.dataset.view));
        });

        // Position buttons
        document.querySelectorAll('.position-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectPosition(e.target.dataset.position));
        });

        // Fetch photos button
        const fetchBtn = document.getElementById('fetch-photos-btn');
        if (fetchBtn) {
            fetchBtn.addEventListener('click', () => this.fetchPhotos());
        }

        // Process button
        const processBtn = document.getElementById('process-btn');
        if (processBtn) {
            processBtn.addEventListener('click', () => this.startProcessing());
        }

        // Select all button
        const selectAllBtn = document.getElementById('select-all-btn');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.toggleSelectAll());
        }

        // File upload
        const uploadZone = document.getElementById('upload-zone');
        const fileInput = document.getElementById('file-input');

        if (uploadZone && fileInput) {
            uploadZone.addEventListener('click', () => fileInput.click());
            uploadZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadZone.classList.add('dragover');
            });
            uploadZone.addEventListener('dragleave', () => {
                uploadZone.classList.remove('dragover');
            });
            uploadZone.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadZone.classList.remove('dragover');
                this.handleFileUpload(e.dataTransfer.files);
            });
            fileInput.addEventListener('change', (e) => {
                this.handleFileUpload(e.target.files);
            });
        }

        // Modal
        const modalClose = document.getElementById('modal-close');
        const modalBackdrop = document.querySelector('.modal-backdrop');

        if (modalClose) {
            modalClose.addEventListener('click', () => this.closeModal());
        }
        if (modalBackdrop) {
            modalBackdrop.addEventListener('click', () => this.closeModal());
        }

        // Preview process button
        const previewProcessBtn = document.getElementById('preview-process-btn');
        if (previewProcessBtn) {
            previewProcessBtn.addEventListener('click', () => this.processPreviewImage());
        }
    }

    // ========================================
    // API Calls
    // ========================================

    async apiCall(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                ...options,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'API request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            this.showToast(error.message, 'error');
            throw error;
        }
    }

    async checkStatus() {
        try {
            const status = await this.apiCall('/api/status');
            this.state.iopaintAvailable = status.iopaint_available;

            if (!status.iopaint_available) {
                this.showToast('IOPaint not installed. Watermark removal will use fallback method.', 'info');
            }
        } catch (error) {
            // Ignore status check errors
        }
    }

    async fetchAlbums() {
        try {
            const data = await this.apiCall('/api/albums');
            this.state.albums = data.albums || [];
            this.populateAlbumSelect();
        } catch (error) {
            // Not authenticated or other error
        }
    }

    async fetchPhotos() {
        const albumSelect = document.getElementById('album-select');
        const albumId = albumSelect?.value || '';

        this.setLoading(true);

        try {
            const data = await this.apiCall(`/api/photos?album_id=${albumId}&page_size=100`);
            this.state.photos = data.photos || [];
            this.renderPhotoGrid();
            this.showToast(`Loaded ${this.state.photos.length} photos`, 'success');
        } catch (error) {
            // Error already handled
        } finally {
            this.setLoading(false);
        }
    }

    async loadLocalPhotos() {
        try {
            const data = await this.apiCall('/api/local-photos');
            const localPhotos = (data.photos || []).map(p => ({
                id: p.name,
                filename: p.name,
                baseUrl: `/images/downloads/${p.name}`,
                isLocal: true,
            }));

            // Merge with existing photos
            this.state.photos = [...this.state.photos, ...localPhotos];
            this.renderPhotoGrid();
        } catch (error) {
            // Ignore errors
        }
    }

    async loadProcessedPhotos() {
        try {
            const data = await this.apiCall('/api/processed-photos');
            this.state.processedPhotos = (data.photos || []).map(p => ({
                id: p.name,
                filename: p.name,
                baseUrl: `/images/processed/${p.name}`,
                isProcessed: true,
            }));
        } catch (error) {
            // Ignore errors
        }
    }

    async handleFileUpload(files) {
        if (!files || files.length === 0) return;

        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }

        this.setLoading(true);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (data.success) {
                this.showToast(`Uploaded ${data.uploaded} files`, 'success');
                await this.loadLocalPhotos();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            this.showToast(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async downloadSelectedPhotos() {
        const photoIds = Array.from(this.state.selectedPhotos).filter(id => {
            const photo = this.state.photos.find(p => p.id === id);
            return photo && !photo.isLocal;
        });

        if (photoIds.length === 0) {
            this.showToast('No Google Photos selected to download', 'info');
            return;
        }

        this.setLoading(true);

        try {
            const data = await this.apiCall('/api/download', {
                method: 'POST',
                body: JSON.stringify({ photo_ids: photoIds }),
            });

            this.showToast(`Downloaded ${data.downloaded} photos`, 'success');
            await this.loadLocalPhotos();
        } catch (error) {
            // Error handled
        } finally {
            this.setLoading(false);
        }
    }

    async startProcessing() {
        // Get selected local files
        const selectedFiles = Array.from(this.state.selectedPhotos)
            .map(id => {
                const photo = this.state.photos.find(p => p.id === id);
                return photo?.isLocal ? photo.filename : null;
            })
            .filter(Boolean);

        if (selectedFiles.length === 0) {
            this.showToast('No local files selected. Select downloaded images to process.', 'info');
            return;
        }

        this.state.isProcessing = true;
        this.showProgressSection(true);

        try {
            const data = await this.apiCall('/api/process', {
                method: 'POST',
                body: JSON.stringify({
                    files: selectedFiles,
                    position: this.state.selectedPosition,
                }),
            });

            this.showToast(`Started processing ${data.total} images`, 'info');
            this.pollProcessingStatus();
        } catch (error) {
            this.state.isProcessing = false;
            this.showProgressSection(false);
        }
    }

    async pollProcessingStatus() {
        if (!this.state.isProcessing) return;

        try {
            const data = await this.apiCall('/api/process/status');

            this.updateProgress(data.current, data.total, data.status);

            if (data.is_processing) {
                setTimeout(() => this.pollProcessingStatus(), 1000);
            } else {
                this.state.isProcessing = false;

                if (data.results) {
                    this.showToast(
                        `Processing complete! ${data.results.success} succeeded, ${data.results.failed} failed`,
                        data.results.failed > 0 ? 'info' : 'success'
                    );
                }

                await this.loadProcessedPhotos();
                this.switchView('processed');
            }
        } catch (error) {
            setTimeout(() => this.pollProcessingStatus(), 2000);
        }
    }

    async processSingleImage(filename) {
        const loading = document.getElementById('preview-loading');
        const processedImg = document.getElementById('preview-processed');
        const downloadBtn = document.getElementById('preview-download-btn');

        if (loading) loading.classList.remove('hidden');

        try {
            const data = await this.apiCall('/api/process/single', {
                method: 'POST',
                body: JSON.stringify({
                    file: filename,
                    position: this.state.selectedPosition,
                }),
            });

            if (data.success) {
                processedImg.src = `/images/processed/${data.output_name}?t=${Date.now()}`;
                downloadBtn.href = `/images/processed/${data.output_name}`;
                downloadBtn.classList.remove('hidden');
                this.showToast('Image processed successfully!', 'success');
                await this.loadProcessedPhotos();
            }
        } catch (error) {
            // Error handled
        } finally {
            if (loading) loading.classList.add('hidden');
        }
    }

    // ========================================
    // UI Updates
    // ========================================

    switchSource(source) {
        this.state.currentSource = source;

        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.source === source);
        });

        document.getElementById('google-source')?.classList.toggle('hidden', source !== 'google');
        document.getElementById('local-source')?.classList.toggle('hidden', source !== 'local');
    }

    switchView(view) {
        this.state.currentView = view;

        document.querySelectorAll('.photo-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });

        this.renderPhotoGrid();
    }

    selectPosition(position) {
        this.state.selectedPosition = position;

        document.querySelectorAll('.position-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.position === position);
        });
    }

    populateAlbumSelect() {
        const select = document.getElementById('album-select');
        if (!select) return;

        // Clear existing options except the first
        while (select.options.length > 1) {
            select.remove(1);
        }

        this.state.albums.forEach(album => {
            const option = document.createElement('option');
            option.value = album.id;
            option.textContent = `${album.title} (${album.mediaItemsCount || 0})`;
            select.appendChild(option);
        });
    }

    renderPhotoGrid() {
        const grid = document.getElementById('photo-grid');
        if (!grid) return;

        const photos = this.state.currentView === 'processed'
            ? this.state.processedPhotos
            : this.state.photos;

        if (photos.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="64" height="64">
                        <path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                    </svg>
                    <h3>${this.state.currentView === 'processed' ? 'No Processed Photos' : 'No Photos Yet'}</h3>
                    <p>${this.state.currentView === 'processed'
                    ? 'Process some images to see them here'
                    : 'Fetch photos from Google Photos or upload local images'}</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = photos.map(photo => this.createPhotoCard(photo)).join('');

        // Bind click events
        grid.querySelectorAll('.photo-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.shiftKey || e.ctrlKey) {
                    this.togglePhotoSelection(card.dataset.id);
                } else {
                    this.openPreview(card.dataset.id);
                }
            });
        });

        this.updateProcessButton();
    }

    createPhotoCard(photo) {
        const isSelected = this.state.selectedPhotos.has(photo.id);
        const imageUrl = photo.baseUrl?.includes('?')
            ? `${photo.baseUrl}&w=300`
            : photo.baseUrl
                ? `${photo.baseUrl}=w300-h300-c`
                : '/static/placeholder.png';

        return `
            <div class="photo-card ${isSelected ? 'selected' : ''}" data-id="${photo.id}">
                <img src="${imageUrl}" alt="${photo.filename || 'Photo'}" loading="lazy">
                <div class="photo-card-checkbox"></div>
                <div class="photo-card-overlay">
                    <span class="photo-card-name">${photo.filename || 'Photo'}</span>
                </div>
            </div>
        `;
    }

    togglePhotoSelection(photoId) {
        if (this.state.selectedPhotos.has(photoId)) {
            this.state.selectedPhotos.delete(photoId);
        } else {
            this.state.selectedPhotos.add(photoId);
        }

        const card = document.querySelector(`.photo-card[data-id="${photoId}"]`);
        card?.classList.toggle('selected', this.state.selectedPhotos.has(photoId));

        this.updateProcessButton();
    }

    toggleSelectAll() {
        const photos = this.state.currentView === 'processed'
            ? this.state.processedPhotos
            : this.state.photos;

        const allSelected = photos.every(p => this.state.selectedPhotos.has(p.id));

        if (allSelected) {
            photos.forEach(p => this.state.selectedPhotos.delete(p.id));
        } else {
            photos.forEach(p => this.state.selectedPhotos.add(p.id));
        }

        this.renderPhotoGrid();
    }

    updateProcessButton() {
        const btn = document.getElementById('process-btn');
        if (btn) {
            const hasLocalSelected = Array.from(this.state.selectedPhotos).some(id => {
                const photo = this.state.photos.find(p => p.id === id);
                return photo?.isLocal;
            });
            btn.disabled = !hasLocalSelected;
        }
    }

    openPreview(photoId) {
        const photo = this.state.photos.find(p => p.id === photoId)
            || this.state.processedPhotos.find(p => p.id === photoId);

        if (!photo) return;

        const modal = document.getElementById('preview-modal');
        const originalImg = document.getElementById('preview-original');
        const processedImg = document.getElementById('preview-processed');
        const downloadBtn = document.getElementById('preview-download-btn');
        const processBtn = document.getElementById('preview-process-btn');

        const imageUrl = photo.baseUrl?.includes('/images/')
            ? photo.baseUrl
            : photo.baseUrl
                ? `${photo.baseUrl}=w800`
                : '/static/placeholder.png';

        originalImg.src = imageUrl;
        this.currentPreviewPhoto = photo;

        // Check if we have a processed version
        const processedPhoto = this.state.processedPhotos.find(p =>
            p.filename?.includes(photo.filename?.replace(/\.[^/.]+$/, ''))
        );

        if (processedPhoto) {
            processedImg.src = processedPhoto.baseUrl;
            downloadBtn.href = processedPhoto.baseUrl;
            downloadBtn.classList.remove('hidden');
            processBtn.textContent = 'Re-process';
        } else {
            processedImg.src = '';
            downloadBtn.classList.add('hidden');
            processBtn.textContent = 'Process This Image';
        }

        // Show/hide process button based on if it's a local file
        processBtn.classList.toggle('hidden', !photo.isLocal);

        modal.classList.remove('hidden');
    }

    closeModal() {
        const modal = document.getElementById('preview-modal');
        modal?.classList.add('hidden');
        this.currentPreviewPhoto = null;
    }

    processPreviewImage() {
        if (this.currentPreviewPhoto?.isLocal) {
            this.processSingleImage(this.currentPreviewPhoto.filename);
        }
    }

    setLoading(loading) {
        this.state.isLoading = loading;
        // Could add loading overlay here
    }

    showProgressSection(show) {
        const section = document.getElementById('progress-section');
        section?.classList.toggle('hidden', !show);
    }

    updateProgress(current, total, status) {
        const fill = document.getElementById('progress-fill');
        const currentEl = document.getElementById('progress-current');
        const totalEl = document.getElementById('progress-total');
        const statusEl = document.getElementById('progress-status');

        const percent = total > 0 ? (current / total) * 100 : 0;

        if (fill) fill.style.width = `${percent}%`;
        if (currentEl) currentEl.textContent = current;
        if (totalEl) totalEl.textContent = total;
        if (statusEl) statusEl.textContent = status;
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const icons = {
            success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>`,
            error: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>`,
            info: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>`,
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            ${icons[type] || icons.info}
            <span class="toast-message">${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WatermarkRemoverApp();
});
