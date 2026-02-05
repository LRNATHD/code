/**
 * PartScout Application Logic
 */

// State
let inventory = [];
let bulkSelectedIds = new Set();

// DOM Elements
const searchInput = document.getElementById('searchInput');
const clearSearchBtn = document.getElementById('clearSearch');
const uploadTrigger = document.getElementById('uploadTrigger');
const fileInput = document.getElementById('csvFileInput');
const resultsArea = document.getElementById('resultsArea');
// statsBar removed
const itemCountSpan = document.getElementById('itemCount');
const clearDataBtn = document.getElementById('clearDataBtn');
const toastEl = document.getElementById('toast');

// Modal Elements
const addManualBtn = document.getElementById('addManualBtn');
const modalOverlay = document.getElementById('modalOverlay');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const manualItemForm = document.getElementById('manualItemForm');

// Bulk Editor Elements
const mainView = document.getElementById('mainView');
const bulkView = document.getElementById('bulkView');
const openBulkBtn = document.getElementById('openBulkBtn');
const closeBulkBtn = document.getElementById('closeBulkBtn');
const bulkList = document.getElementById('bulkList');
const bulkSelectAll = document.getElementById('bulkSelectAll');
const bulkShowNoLoc = document.getElementById('bulkShowNoLoc');
const applyBulkBtn = document.getElementById('applyBulkLocationBtn');
const bulkLocInput = document.getElementById('bulkLocationInput');
const bulkSelectedCount = document.getElementById('bulkSelectedCount');


// Smart Tags Configuration
const TAG_RULES = [
    { label: 'Keyboard Switch', regex: /(key|mech|push)\s*switch|cherry|gateron|kailh|\d+gf/i },
    { label: 'Resistor', regex: /\b\d+(\.\d+)?[kM]?\s*[\u2126\u03A9oO]hm|\bres\b|resistor/i },
    { label: 'Capacitor', regex: /\b\d+(\.\d+)?[n\u00B5u]F|\bcap\b|capacitor/i },
    { label: 'Inductor', regex: /\b\d+(\.\d+)?[n\u00B5u]H|\bind\b|inductor/i },
    { label: 'Diode', regex: /\bdiode\b|\brectifier\b|1N4\d{3}/i },
    { label: 'LED', regex: /\bled\b|\blayer\semitting\b/i },
    { label: 'MCU', regex: /\bmcu\b|\bmicrocontroller\b|stm32|esp32|atmega|pic1|ch32|ch5/i },
    { label: 'Connector', regex: /\bheader\b|\bconn\b|\bsocket\b|usb|jst/i },
    { label: 'IC', regex: /\bic\b|\bchip\b|sop-|qfn-|dip-/i },
];

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    setupEventListeners();
});

function setupEventListeners() {
    // Search
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value;
        if (query.trim() === '') {
            renderResults([], false);
        } else {
            handleSearch(query);
        }
    });

    clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.focus();
        renderResults([], false);
    });

    // File Upload
    uploadTrigger.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);

    // Data Management
    clearDataBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all inventory data? This will be saved to the server immediately.')) {
            inventory = [];
            saveData();
            showToast('All data cleared.');
            renderResults([], false);
        }
    });

    // Modal Interaction
    addManualBtn.addEventListener('click', () => {
        modalOverlay.classList.remove('hidden');
        document.getElementById('mPartNum').focus();
    });

    cancelModalBtn.addEventListener('click', () => {
        modalOverlay.classList.add('hidden');
        manualItemForm.reset();
    });

    // Quick Source Buttons
    document.querySelectorAll('.quick-source-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.getElementById('mSource').value = btn.getAttribute('data-value');
        });
    });

    // Manual Form Submit
    manualItemForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const newItem = {
            id: generateId(),
            source: document.getElementById('mSource').value,
            partNumber: document.getElementById('mPartNum').value,
            manufacturer: document.getElementById('mMfr').value,
            description: document.getElementById('mDesc').value,
            quantity: document.getElementById('mQty').value,
            location: document.getElementById('mLoc').value,
            link: document.getElementById('mLink').value,
            orderDate: new Date().toISOString().split('T')[0], // Today YYYY-MM-DD
            mfrPart: '', // Derived if needed, or left empty
        };

        // Generate tags for the new item
        newItem.tags = generateTags(`${newItem.description} ${newItem.manufacturer} ${newItem.partNumber}`);
        // If mfr part is blank, maybe assume partNumber is mfrPart for manual entries?
        if (!newItem.mfrPart) newItem.mfrPart = newItem.partNumber;

        inventory.unshift(newItem); // Add to top
        saveData();
        showToast('Item Added Successfully');

        modalOverlay.classList.add('hidden');
        manualItemForm.reset();

        // If visible results, refresh
        if (searchInput.value.trim() !== '') {
            handleSearch(searchInput.value);
        }
    });

    setupBulkEditor();
}

function setupBulkEditor() {
    // Toggle Views
    openBulkBtn.addEventListener('click', () => {
        mainView.classList.add('hidden');
        bulkView.classList.remove('hidden');
        renderBulkList();
    });

    closeBulkBtn.addEventListener('click', () => {
        bulkView.classList.add('hidden');
        mainView.classList.remove('hidden');
        // Refresh main view if search is active since locations might have changed
        if (searchInput.value.trim() !== '') {
            handleSearch(searchInput.value);
        } else {
            renderResults([], false); // Refresh random selection
        }
    });

    // Filtering
    bulkShowNoLoc.addEventListener('change', renderBulkList);

    // Selection
    bulkSelectAll.addEventListener('change', (e) => {
        const checkboxes = bulkList.querySelectorAll('.bulk-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = e.target.checked;
            if (e.target.checked) bulkSelectedIds.add(cb.getAttribute('data-id'));
            else bulkSelectedIds.delete(cb.getAttribute('data-id'));
        });
        updateBulkCount();
    });

    // Apply Location
    applyBulkBtn.addEventListener('click', () => {
        const newLoc = bulkLocInput.value.trim();
        if (!newLoc) return alert('Please enter a location first.');
        if (bulkSelectedIds.size === 0) return alert('No items selected.');

        let count = 0;
        inventory.forEach(item => {
            if (bulkSelectedIds.has(item.id)) {
                item.location = newLoc;
                count++;
            }
        });

        saveData();
        showToast(`Updated location for ${count} items.`);

        // Reset
        bulkSelectedIds.clear();
        bulkLocInput.value = '';
        bulkSelectAll.checked = false;
        renderBulkList(); // Re-render to update UI (loc column) or remove if filtered
    });
}

function updateBulkCount() {
    bulkSelectedCount.textContent = `${bulkSelectedIds.size} selected`;
}

// Render List
function renderBulkList() {
    bulkList.innerHTML = '';
    bulkSelectedIds.clear(); // Reset selection on re-render to avoid ghost selections
    bulkSelectAll.checked = false;
    updateBulkCount();

    const showOnlyNoLoc = bulkShowNoLoc.checked;

    const filteredInventory = showOnlyNoLoc
        ? inventory.filter(i => !i.location || i.location.trim() === '')
        : inventory;

    // Limit to 500 for performance
    const displayItems = filteredInventory.slice(0, 500);

    if (displayItems.length === 0) {
        bulkList.innerHTML = '<div style="text-align:center; padding:20px; color:var(--text-muted);">No items found matching criteria.</div>';
        return;
    }

    displayItems.forEach(item => {
        const row = document.createElement('div');
        row.style.cssText = `
            display:flex; align-items:center; gap:12px; 
            padding:12px; background:rgba(30,41,59,0.5); 
            border:1px solid var(--border-color); border-radius:8px;
        `;

        // Determine Title
        let title = item.mfrPart;
        if (!title || title === item.partNumber) {
            if (item.manufacturer && item.partNumber) title = `${item.manufacturer} ${item.partNumber}`;
            else title = item.partNumber || 'Unknown Part';
        }

        // Checkbox
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.className = 'bulk-checkbox';
        cb.setAttribute('data-id', item.id);
        cb.style.cssText = 'width:18px; height:18px; cursor:pointer; accent-color:var(--accent-primary);';

        cb.addEventListener('change', (e) => {
            if (e.target.checked) bulkSelectedIds.add(item.id);
            else bulkSelectedIds.delete(item.id);
            updateBulkCount();
        });

        // Text Info
        const info = document.createElement('div');
        info.style.flexGrow = '1';
        info.innerHTML = `
            <div style="font-weight:600; font-size:0.95rem; color:#fff;">${escapeHtml(title)}</div>
            <div style="font-size:0.8rem; color:var(--text-muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:60vw;">
                ${escapeHtml(item.description || '')}
            </div>
        `;

        // Current Location Badge
        const locBadge = document.createElement('div');
        if (item.location) {
            locBadge.textContent = item.location;
            locBadge.style.cssText = 'background:rgba(255,255,255,0.15); padding:4px 8px; border-radius:12px; font-size:0.75rem; color:#fff; white-space:nowrap;';
        } else {
            locBadge.textContent = 'No Loc';
            locBadge.style.cssText = 'background:rgba(239,68,68,0.2); padding:4px 8px; border-radius:12px; font-size:0.75rem; color:#f87171; white-space:nowrap;';
        }

        row.appendChild(cb);
        row.appendChild(info);
        row.appendChild(locBadge);

        bulkList.appendChild(row);
    });

    if (filteredInventory.length > 500) {
        const more = document.createElement('div');
        more.textContent = `...and ${filteredInventory.length - 500} more items hidden for performance.`;
        more.style.cssText = 'text-align:center; padding:10px; color:var(--text-muted); font-size:0.8rem;';
        bulkList.appendChild(more);
    }
}


// --- Data & Server Sync ---

function loadData() {
    fetch('/api/inventory')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Assign IDs to existing items if missing (migration)
            inventory = data.map(item => {
                if (!item.id) item.id = generateId();
                return item;
            });
            updateStats();
            console.log('Loaded inventory from server:', inventory.length, 'items');
            renderResults([], false); // Initial render with random items
        })
        .catch(error => {
            console.warn('Could not load from server', error);
            const raw = localStorage.getItem('partscout_db_v3');
            if (raw) {
                const data = JSON.parse(raw);
                inventory = data.map(item => {
                    if (!item.id) item.id = generateId();
                    return item;
                });
                updateStats();
                showToast('Offline Mode: Loaded from Browser Storage');
                renderResults([], false); // Initial render with random items
            }
        });
}

function saveData() {
    localStorage.setItem('partscout_db_v3', JSON.stringify(inventory));
    updateStats();

    fetch('/api/inventory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(inventory),
    })
        .catch(error => {
            console.error('Network error saving to server', error);
        });
}

function updateStats() {
    if (inventory.length > 0) {
        // statsBar removed, just update text
        if (itemCountSpan) {
            itemCountSpan.textContent = `${inventory.length.toLocaleString()} items tracked`;
            itemCountSpan.style.display = 'inline';
        }
        if (clearDataBtn) clearDataBtn.style.display = 'inline-block';
    } else {
        if (itemCountSpan) itemCountSpan.style.display = 'none';
        if (clearDataBtn) clearDataBtn.style.display = 'none';
    }
}


function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

// --- Search Logic ---

function handleSearch(query) {
    const originalTerm = query.toLowerCase().trim();
    if (!originalTerm) return;

    // Expand terms with conversions
    const searchTerms = expandSearchTerm(originalTerm);

    // Improved search
    const results = inventory.filter(item => {
        const part = (item.partNumber || '').toLowerCase();
        const desc = (item.description || '').toLowerCase();
        const mfr = (item.mfrPart || '').toLowerCase();
        const brand = (item.manufacturer || '').toLowerCase();
        const loc = (item.location || '').toLowerCase();
        const tags = (item.tags || []).join(' ').toLowerCase();
        const source = (item.source || '').toLowerCase();

        return searchTerms.some(term =>
            part.includes(term) ||
            desc.includes(term) ||
            mfr.includes(term) ||
            brand.includes(term) ||
            loc.includes(term) ||
            source.includes(term) ||
            tags.includes(term)
        );
    });

    // Sort by relevance
    results.sort((a, b) => {
        const aExact = (a.partNumber || '').toLowerCase() === originalTerm;
        const bExact = (b.partNumber || '').toLowerCase() === originalTerm;
        if (aExact && !bExact) return -1;
        if (!aExact && bExact) return 1;

        return new Date(b.orderDate) - new Date(a.orderDate);
    });

    renderResults(results.slice(0, 50), true);
}

function expandSearchTerm(term) {
    const variations = new Set([term]);

    // Capacitance: (\d+(\.\d+)?)\s*(uF|nF|pF)
    const capMatch = term.match(/^(\d+(\.\d+)?)\s*([unpµ])f$/i);
    if (capMatch) {
        const val = parseFloat(capMatch[1]);
        const unit = capMatch[3].toLowerCase().replace('µ', 'u'); // normalize

        let pF_val;
        if (unit === 'u') pF_val = val * 1_000_000;
        else if (unit === 'n') pF_val = val * 1_000;
        else if (unit === 'p') pF_val = val;

        // Generate nF
        if (pF_val >= 1000 && pF_val < 1_000_000_000) {
            const nf = pF_val / 1000;
            variations.add(`${nf}nf`);
            variations.add(`${nf} nf`);
        }
        // Generate uF
        if (pF_val >= 1_000_000) {
            const uf = pF_val / 1_000_000;
            variations.add(`${uf}uf`);
            variations.add(`${uf} uf`);
        }
        // Generate pF
        if (pF_val < 1000000) {
            variations.add(`${pF_val}pf`);
            variations.add(`${pF_val} pf`);
        }
    }

    // Resistance: (\d+(\.\d+)?)\s*(k|m|r|ohm)?
    // "5.1k"
    const resMatch = term.match(/^(\d+(\.\d+)?)\s*(k|m)?(ohm|r|[\u2126\u03A9])?$/i);
    if (resMatch && (resMatch[3] || resMatch[4])) {
        const val = parseFloat(resMatch[1]);
        const suffix = (resMatch[3] || '').toLowerCase();

        let ohms;
        if (suffix === 'k') ohms = val * 1000;
        else if (suffix === 'm') ohms = val * 1_000_000;
        else ohms = val;

        const clean = n => parseFloat(n.toPrecision(12));

        if (ohms >= 1_000_000) {
            const mVal = clean(ohms / 1_000_000);
            variations.add(`${mVal}m`);
            variations.add(`${mVal}m ohm`);
        }
        if (ohms >= 1000) {
            const kVal = clean(ohms / 1000);
            variations.add(`${kVal}k`);
            variations.add(`${kVal}k ohm`);
        }

        variations.add(`${clean(ohms)}`);
        variations.add(`${clean(ohms)}r`);
        variations.add(`${clean(ohms)}ohm`);
    }

    return Array.from(variations);
}

function renderResults(items, isSearch = false) {
    resultsArea.innerHTML = '';

    // If search is empty and no items passed (initial load or clear), show random selection
    if (!isSearch && inventory.length > 0 && searchInput.value.trim() === '') {
        // Show random assortment
        const shuffled = [...inventory].sort(() => 0.5 - Math.random());
        items = shuffled.slice(0, 50); // Show 50 random items
        // Header REMOVED as requested
    } else if (searchInput.value.trim() === '' && items.length === 0) {
        // Only show empty state if inventory is truly empty
        if (inventory.length === 0) {
            resultsArea.innerHTML = `
                <div class="empty-state">
                    <div class="icon">📦</div>
                    <h3>No Parts Found</h3>
                    <p>Try searching for a component or upload a CSV file to get started.</p>
                </div>
            `;
            return;
        }
    } else if (items.length === 0) {
        // Search yielded no results
        resultsArea.innerHTML = `
            <div class="empty-state">
                <div class="icon">🤷‍♂️</div>
                <h3>No Matches Found</h3>
                <p>Try searching manually or check your spelling.</p>
            </div>
        `;
        return;
    }

    items.forEach(item => {
        const card = document.createElement('div');
        const sourceClass = item.source ? item.source.toLowerCase() : 'unknown';
        card.className = `result-card source-${sourceClass}`;

        // Logic for displaying best possible title
        let title = item.mfrPart;
        if (!title || title === item.partNumber) {
            if (item.manufacturer && item.partNumber) title = `${item.manufacturer} ${item.partNumber}`;
            else title = item.partNumber || 'Unknown Part';
        }

        const subtitle = item.description || (item.mfrPart ? item.partNumber : '');
        const brand = item.manufacturer ? `<div class="brand-tag">${item.manufacturer}</div>` : '';

        const tagsHtml = (item.tags || []).map(t => `<span class="smart-tag">${t}</span>`).join('');

        // Source Badge
        let sourceBadge = '';
        if (item.source === 'LCSC') sourceBadge = '<span class="source-badge lcsc">LCSC</span>';
        else if (item.source === 'DigiKey') sourceBadge = '<span class="source-badge digikey">DigiKey</span>';
        else sourceBadge = `<span class="source-badge other">${item.source}</span>`;

        // Link Button
        let linkBtn = '';
        if (item.link) {
            linkBtn = `<a href="${item.link}" target="_blank" class="action-btn" title="View on Supplier Site" onclick="event.stopPropagation()">↗</a>`;
        }

        const clickAttr = item.link ? `onclick="window.open('${item.link}', '_blank')"` : '';
        if (item.link) card.style.cursor = 'pointer';

        card.innerHTML = `
            <div class="card-header">
                <div style="display:flex; gap:8px; align-items:center;">
                    ${sourceBadge}
                    ${brand}
                </div>
                ${linkBtn}
            </div>
            
            <div class="card-body" ${clickAttr}>
                <div class="part-name" title="${title}">${escapeHtml(title)}</div>
                <div class="part-desc" title="${subtitle}">${escapeHtml(subtitle)}</div>
                
                <div class="tags-container">
                    ${tagsHtml}
                </div>

                <div class="part-meta">
                    <span class="qty-badge">${item.quantity ? item.quantity + ' pcs' : 'N/A'}</span>
                    <span class="date">${formatDate(item.orderDate)}</span>
                </div>
                
                <div onclick="event.stopPropagation()">
                    <input type="text" class="location-input" placeholder="Set Location (e.g. Box 1)" 
                           value="${escapeHtml(item.location)}" 
                           data-id="${item.id}">
                </div>
            </div>
        `;

        // Attach event listener for location input
        const locInput = card.querySelector('.location-input');
        locInput.addEventListener('change', (e) => {
            const newLoc = e.target.value;
            updateItemLocation(item.id, newLoc);
        });

        resultsArea.appendChild(card);
    });
}

function updateItemLocation(id, location) {
    const item = inventory.find(i => i.id === id);
    if (item) {
        item.location = location;
        saveData();
    }
}

function formatDate(dateStr) {
    if (!dateStr || dateStr === 'Invalid Date' || dateStr === '') return 'Unknown Date';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return 'Unknown Date';
    return d.toLocaleDateString();
}

// --- CSV Parsing ---

function handleFileUpload(e) {
    const files = e.target.files;
    if (!files.length) return;

    let processedCount = 0;
    const totalFiles = files.length;

    Array.from(files).forEach(file => {
        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target.result;
            const newItems = parseCSV(text, file.name);

            if (newItems.length > 0) {
                const source = newItems[0].source;
                inventory = [...inventory, ...newItems];
                saveData();
                showToast(`Imported ${newItems.length} items (${source})`);

                // If first import, refresh view to show items
                if (inventory.length === newItems.length) {
                    renderResults([], false);
                }
            } else {
                showToast(`Could not recognize data in ${file.name}`);
            }

            processedCount++;
            if (processedCount === totalFiles) {
                fileInput.value = '';
            }
        };
        reader.readAsText(file);
    });
}

function parseCSV(text, filename) {
    const rows = [];
    let currentRow = [];
    let currentCell = '';
    let inQuotes = false;

    for (let i = 0; i < text.length; i++) {
        const char = text[i];
        const nextChar = text[i + 1];

        if (char === '"') {
            if (inQuotes && nextChar === '"') {
                currentCell += '"';
                i++;
            } else {
                inQuotes = !inQuotes;
            }
        } else if (char === ',' && !inQuotes) {
            currentRow.push(currentCell.trim());
            currentCell = '';
        } else if ((char === '\r' || char === '\n') && !inQuotes) {
            if (currentCell || currentRow.length > 0) {
                currentRow.push(currentCell.trim());
                rows.push(currentRow);
                currentRow = [];
                currentCell = '';
            }
            if (char === '\r' && nextChar === '\n') i++;
        } else {
            currentCell += char;
        }
    }
    if (currentCell || currentRow.length > 0) {
        currentRow.push(currentCell.trim());
        rows.push(currentRow);
    }

    if (rows.length < 2) return [];

    const headers = rows[0].map(h => h.toLowerCase().replace(/[^a-z0-9]/g, ''));
    let isLCSC = headers.some(h => h.includes('lcscpart'));
    let isDigiKey = headers.some(h => h.includes('digikeypart'));

    if (!isLCSC && !isDigiKey) {
        if (text.includes('LCSC Part #')) isLCSC = true;
        else if (text.includes('Digi-Key Part Number')) isDigiKey = true;
    }

    const source = isLCSC ? 'LCSC' : (isDigiKey ? 'DigiKey' : 'Unknown');

    const colMap = {
        partNumber: headers.findIndex(h => h.includes('lcscpart') || h.includes('digikeypart') || h.includes('partnumber') || h.includes('part') || h === 'part'),
        mfrPart: headers.findIndex(h => h.includes('manufacturepart') || h.includes('mfrpart') || h.includes('productname') || h.includes('mfr.')),
        manufacturer: headers.findIndex(h => h === 'manufacturer' || h.includes('brand') || h.includes('vendor')),
        description: headers.findIndex(h => h.includes('description') || h.includes('detail') || h.includes('parameter') || h.includes('comment')),
        quantity: headers.findIndex(h => h.includes('quantity') || h.includes('qty') || h.includes('orderqty')),
        orderDate: headers.findIndex(h => h.includes('ordertime') || h.includes('date') || h.includes('time') || h.includes('placed') || h.includes('invoice'))
    };

    const items = [];
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        if (row.length < 2) continue;

        let rawPart = colMap.partNumber > -1 ? row[colMap.partNumber] : '';
        let rawMfr = colMap.mfrPart > -1 ? row[colMap.mfrPart] : '';
        let rawBrand = colMap.manufacturer > -1 ? row[colMap.manufacturer] : '';
        let rawDesc = colMap.description > -1 ? row[colMap.description] : '';
        let rawDate = colMap.orderDate > -1 ? row[colMap.orderDate] : '';
        let rawQty = colMap.quantity > -1 ? row[colMap.quantity] : '';

        const clean = (str) => (str || '').replace(/^"|"$/g, '').trim();

        rawPart = clean(rawPart);
        rawMfr = clean(rawMfr);
        rawBrand = clean(rawBrand);
        rawDesc = clean(rawDesc);

        if (!rawMfr && !rawPart && !rawDesc) continue;

        let finalDate = undefined;
        // Parse date from row
        if (rawDate) {
            const d = new Date(rawDate.replace(/"/g, '').trim());
            if (!isNaN(d.getTime())) finalDate = d.toISOString();
        }

        // LCSC fallback from filename
        if ((!finalDate || finalDate === 'Invalid Date') && filename) {
            const fileDateMatch = filename.match(/(\d{4})(\d{2})(\d{2})\d{6}/);
            if (fileDateMatch) {
                finalDate = `${fileDateMatch[1]}-${fileDateMatch[2]}-${fileDateMatch[3]}`;
            } else {
                const simpleDate = filename.match(/20\d{6}/);
                if (simpleDate) {
                    const s = simpleDate[0];
                    finalDate = `${s.substring(0, 4)}-${s.substring(4, 6)}-${s.substring(6, 8)}`;
                }
            }
        }

        const combinedText = `${rawDesc} ${rawMfr} ${rawPart} ${rawBrand}`;
        const tags = generateTags(combinedText);

        let link = '';
        if (isLCSC && (rawPart.startsWith('C') || rawPart.match(/^C\d+$/))) {
            link = `https://www.lcsc.com/product-detail/_${rawPart}.html`;
        } else if (isDigiKey) {
            link = `https://www.digikey.com/en/products/result?keywords=${encodeURIComponent(rawPart || rawMfr)}`;
        }

        const item = {
            id: generateId(), // Unique ID for each item
            partNumber: rawPart,
            mfrPart: rawMfr,
            manufacturer: rawBrand,
            description: rawDesc,
            quantity: rawQty.replace(/[^0-9]/g, ''),
            orderDate: finalDate,
            source: source,
            tags: tags,
            link: link,
            location: '' // Initialize as empty
        };

        items.push(item);
    }

    return items;
}

function generateTags(text) {
    let tags = [];
    const t = text.toLowerCase();
    TAG_RULES.forEach(rule => {
        if (rule.regex.test(t)) tags.push(rule.label);
    });

    // Filtering: If recognized as Inductor, ignore Resistor match (likely DCR spec)
    if (tags.includes('Inductor') && tags.includes('Resistor')) {
        tags = tags.filter(t => t !== 'Resistor');
    }

    return [...new Set(tags)];
}

function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return unsafe || '';
    return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function showToast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.remove('hidden');
    setTimeout(() => {
        toastEl.classList.add('hidden');
    }, 3000);
}
