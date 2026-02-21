import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS3DRenderer, CSS3DObject } from 'three/addons/renderers/CSS3DRenderer.js';

// --- State ---
let inventory = [];
let camera, scene, renderer;
let controls;
let sceneGroup;

// DOM Elements
const searchInput = document.getElementById('searchInput');
const clearSearch = document.getElementById('clearSearch');
const resultsArea = document.getElementById('resultsArea');
const csvFileInput = document.getElementById('csvFileInput');
const uploadTrigger = document.getElementById('uploadTrigger');
const resetViewBtn = document.getElementById('resetViewBtn');
const itemCountSpan = document.getElementById('itemCount');
const clearDataBtn = document.getElementById('clearDataBtn');
const manualItemForm = document.getElementById('manualItemForm');
const modalOverlay = document.getElementById('modalOverlay');
const addManualBtn = document.getElementById('addManualBtn');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const boxEditModal = document.getElementById('boxEditModal');
const boxEditForm = document.getElementById('boxEditForm');
const cancelBoxEditBtn = document.getElementById('cancelBoxEditBtn');
const deleteBoxItemBtn = document.getElementById('deleteBoxItemBtn');

// Inputs for Edit Modal
const editItemIdInput = document.getElementById('editItemId');
const editLabelMainInput = document.getElementById('editLabelMain');
const editLabelSubInput = document.getElementById('editLabelSub');
const editLabelSizeInput = document.getElementById('editLabelSize');

// Initialize
init();

function init() {
    loadData();
    setupEventListeners();
    init3D();
    setupSearch();
}

function loadData() {
    const stored = localStorage.getItem('partscout_db_v3');
    if (stored) {
        inventory = JSON.parse(stored);
    }
    updateStats();
}

function saveData() {
    localStorage.setItem('partscout_db_v3', JSON.stringify(inventory));
    updateStats();
}

// --- 3D Logic ---

function init3D() {
    const container = document.getElementById('canvas-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // SCENE
    scene = new THREE.Scene();
    sceneGroup = new THREE.Group();
    scene.add(sceneGroup);

    // CAMERA
    camera = new THREE.PerspectiveCamera(50, width / height, 1, 5000);
    camera.position.set(0, 0, 1500); // Start zoomed out, facing front

    // RENDERER (CSS3D)
    renderer = new CSS3DRenderer();
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    // CONTROLS
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 200;
    controls.maxDistance = 3000;
    // Limit rotation to be mostly frontal but allow 3D inspection
    controls.maxPolarAngle = Math.PI / 1.5;
    controls.minPolarAngle = Math.PI / 4;

    // GENERATE BOXES
    createPhysicalBox();

    // Loop
    animate();

    // Resize
    window.addEventListener('resize', () => {
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });

    // Reset View Button
    if (resetViewBtn) {
        resetViewBtn.addEventListener('click', () => {
            controls.reset();
            camera.position.set(0, 0, 1500);
            camera.lookAt(0, 0, 0);
        });
    }
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

function createPhysicalBox() {
    sceneGroup.clear();

    // CONFIGURATION
    // Defined to simulate physical size
    const BOX_WIDTH = 1200; // Global Width Units
    const TOP_ROWS = 6;
    const TOP_COLS = 12;
    const BOT_ROWS = 4;
    const BOT_COLS = 6;
    const GAP = 40; // Gap between Top and Bottom Segment

    console.log('Initializing 3D Box Geometry (v24)...');

    // Dimensions
    const topCellW = BOX_WIDTH / TOP_COLS;
    const topCellH = 100; // Arbitrary height per row
    // Top Total Height = 600

    // Bottom Segment must match Width = 1200
    // But has only 6 cols. So Cell Width is Double.
    const botCellW = BOX_WIDTH / BOT_COLS;
    // Bottom Rows = 4. Let's assume the bottom tray is same physical HEIGHT as top.
    const botCellH = (TOP_ROWS * topCellH) / BOT_ROWS; // 600 / 4 = 150

    // --- GENERATE TOP SEGMENT ---
    const topGroup = new THREE.Group();
    // Centering offset
    const topOffsetX = -(TOP_COLS * topCellW) / 2 + (topCellW / 2);
    const topOffsetY = (TOP_ROWS * topCellH) / 2 - (topCellH / 2);

    for (let r = 0; r < TOP_ROWS; r++) {
        for (let c = 0; c < TOP_COLS; c++) {
            // Row 1 is Top. (0 index)
            // Label: r=0 -> Row 1.
            const labelShort = `T${r + 1}-${c + 1}`;
            const locName = `Top ${r + 1}-${c + 1}`;

            const object = createCellObject(locName, labelShort, topCellW, topCellH);

            // X: Col Index
            // Y: Row Index (Top is High Y)
            object.position.x = topOffsetX + (c * topCellW);
            object.position.y = topOffsetY - (r * topCellH);
            object.position.z = 0;

            topGroup.add(object);
        }
    }
    // Shift Top Group Up
    topGroup.position.y = (TOP_ROWS * topCellH) / 2 + (GAP / 2);
    sceneGroup.add(topGroup);


    // --- GENERATE BOTTOM SEGMENT ---
    const botGroup = new THREE.Group();
    // Width is constant
    const botOffsetX = -(BOT_COLS * botCellW) / 2 + (botCellW / 2);

    // Height Calculation:
    // Rows 1 & 2: Height = 200
    // Rows 3 & 4: Height = 100
    // Total = 600.
    // Center Y is at 300 from top.

    const rowHeights = [200, 200, 100, 100];
    let currentY = 300; // Start at Top of the Bottom Segment (local +300)

    for (let r = 0; r < BOT_ROWS; r++) {
        const h = rowHeights[r];
        // Center of this row is currentY - (h/2)
        const centerY = currentY - (h / 2);

        for (let c = 0; c < BOT_COLS; c++) {
            const labelShort = `B${r + 1}-${c + 1}`;
            const locName = `Bottom ${r + 1}-${c + 1}`;

            const object = createCellObject(locName, labelShort, botCellW, h);

            object.position.x = botOffsetX + (c * botCellW);
            object.position.y = centerY;
            object.position.z = 0;

            botGroup.add(object);
        }

        currentY -= h; // Move down for next row
    }

    // Shift Bottom Group Down (Center to Center distance)
    // Top is centered at Y=0 (local). Bottom starts at Y=300 local?? 
    // Wait, topGroup was shifted by +height/2 + gap.
    // Let's position botGroup center.
    // Its total height is 600. Center is 0.
    // We want its Top Edge to be at TopGroup Bottom Edge + Gap.
    // TopGroup Bottom Edge = (TOP_ROWS*100)/2 = -300 ?? No.
    // Let's simplify.

    // Top Group Center Y = +310 (300 + 10).
    // Bottom Group Center Y = -310 (-300 - 10).
    botGroup.position.y = -((600 / 2) + (GAP / 2));
    sceneGroup.add(botGroup);
}

function createCellObject(locName, labelShort, width, height) {
    // 1. Create DOM Element
    const div = document.createElement('div');
    div.className = 'box-cell-3d';
    div.style.width = (width - 4) + 'px'; // -4 for spacing/border
    div.style.height = (height - 4) + 'px';
    div.style.background = '#1a1a1a';
    div.style.border = '1px solid #333';
    div.style.borderRadius = '8px';
    div.style.boxSizing = 'border-box';
    div.style.position = 'relative'; // For content

    // Dataset for Logic
    div.dataset.loc = locName; // "Top 1-1"
    div.dataset.short = labelShort; // "T1-1"

    // Populate Content
    updateCellContent(div, locName, labelShort);

    // 2. Drag & Drop Logic (Native HTML5 on the DOM element)
    div.addEventListener('dragover', (e) => {
        e.preventDefault();
        div.style.borderColor = 'var(--accent-primary)';
        div.style.background = 'rgba(100, 108, 255, 0.1)';
        e.dataTransfer.dropEffect = 'move';
    });

    div.addEventListener('dragleave', () => {
        div.style.borderColor = '#333'; // Revert
        div.style.background = '#1a1a1a';
    });

    div.addEventListener('drop', (e) => {
        e.preventDefault();
        div.style.borderColor = '#333';
        div.style.background = '#1a1a1a';

        const itemId = e.dataTransfer.getData('text/plain');
        if (itemId) {
            handleDropItem(itemId, locName);
        }
    });

    // 3. Click Logic
    div.addEventListener('click', () => {
        const item = inventory.find(i => i.location === "Box " + locName);
        if (item) {
            openLabelEditor(item);
        }
    });

    // 4. Wrap in CSS3DObject
    const object = new CSS3DObject(div);
    return object;
}

function updateCellContent(div, locName, labelShort) {
    const item = inventory.find(i => i.location === "Box " + locName);

    if (item) {
        div.classList.add('has-item');
        // Source Styling
        div.style.borderLeft = 'none'; // Reset
        let borderStyle = '';
        if ((item.source || '').toLowerCase().includes('lcsc')) {
            div.style.borderLeft = '4px solid var(--lcsc-color)';
        } else if ((item.source || '').toLowerCase().includes('digikey')) {
            div.style.borderLeft = '4px solid var(--digikey-color)';
        }

        const desc = item.description || item.mfrPart || 'No Description';
        const mfr = item.manufacturer ? `<span class="brand-tag">${escapeHtml(item.manufacturer)}</span>` : '';

        // Mini Card HTML (Same as before)
        div.innerHTML = `
            <div class="mini-card" style="padding: 8px; height:100%; display:flex; flex-direction:column; gap:2px;">
                <div class="result-header" style="display:flex; justify-content:space-between;">
                    <span class="part-number" style="font-weight:600; color:var(--accent-secondary); font-size:0.9rem;">${escapeHtml(item.partNumber)}</span>
                    <span class="quantity-badge" style="font-size:0.7rem;">${item.quantity}</span>
                </div>
                <div class="result-desc" style="color:#aaa; font-size:0.75rem; overflow:hidden; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical;">${escapeHtml(desc)}</div>
                ${mfr}
                <div style="margin-top:auto; font-size:0.65rem; color:#444; align-self:flex-end;">${labelShort}</div>
            </div>
        `;
    } else {
        div.classList.remove('has-item');
        div.innerHTML = `<div style="display:flex; justify-content:center; align-items:center; height:100%; color:#333; font-weight:600; font-size:1.2rem;">${labelShort}</div>`;
        div.style.borderLeft = '1px solid #333';
    }
}

function handleDropItem(itemId, location) {
    const item = inventory.find(i => i.id === itemId);
    if (!item) return;

    item.location = "Box " + location;
    saveData();
    showToast(`Moved "${item.partNumber}" to ${item.location}`);

    // Re-render ALL cells (brute force but safe)
    const domObjects = document.querySelectorAll('.box-cell-3d');
    domObjects.forEach(d => {
        updateCellContent(d, d.dataset.loc, d.dataset.short);
    });

    // Update List Input if visible
    const input = document.querySelector(`.location-input[data-id="${itemId}"]`);
    if (input) input.value = item.location;
}


// --- Standard Logic (Sidebar, Search, etc.) ---

function setupEventListeners() {
    // Search
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        renderList(inventory.filter(i => matchSearch(i, term)));
        clearSearch.style.display = term ? 'block' : 'none';
    });

    clearSearch.addEventListener('click', () => {
        searchInput.value = '';
        renderList(inventory);
        clearSearch.style.display = 'none';
        searchInput.focus();
    });

    // Modals
    addManualBtn.addEventListener('click', () => {
        modalOverlay.classList.remove('hidden');
    });

    cancelModalBtn.addEventListener('click', () => {
        modalOverlay.classList.add('hidden');
    });

    manualItemForm.addEventListener('submit', (e) => {
        e.preventDefault();
        // Add Logic Simplified
        const newItem = {
            id: Date.now().toString(), // Simple ID
            partNumber: document.getElementById('mPartNum').value,
            description: document.getElementById('mDesc').value,
            quantity: 1,
            addedDate: new Date().toISOString()
        };
        inventory.push(newItem);
        saveData();
        renderList(inventory);
        modalOverlay.classList.add('hidden');
        manualItemForm.reset();
    });

    // Box Edit Modal Buttons
    cancelBoxEditBtn.addEventListener('click', () => {
        boxEditModal.classList.add('hidden');
    });

    // Deletion
    deleteBoxItemBtn.addEventListener('click', () => {
        const id = editItemIdInput.value;
        inventory = inventory.filter(i => i.id !== id);
        saveData();
        boxEditModal.classList.add('hidden');
        renderList(inventory);

        // Update 3D
        const domObjects = document.querySelectorAll('.box-cell-3d');
        domObjects.forEach(d => updateCellContent(d, d.dataset.loc, d.dataset.short));
    });
}

function setupSearch() {
    renderList(inventory);
}

function matchSearch(item, term) {
    if (!term) return true;
    const txt = `${item.partNumber} ${item.description} ${item.manufacturer || ''} ${item.location || ''}`.toLowerCase();
    return txt.includes(term);
}

function renderList(items) {
    resultsArea.innerHTML = '';
    itemCountSpan.textContent = `${items.length} items`;

    if (items.length === 0) {
        resultsArea.innerHTML = `<div class="empty-state"><p>No items found.</p></div>`;
        return;
    }

    const frag = document.createDocumentFragment();
    items.forEach(item => {
        const card = createCard(item);
        frag.appendChild(card);
    });
    resultsArea.appendChild(frag);
}

function createCard(item) {
    const el = document.createElement('div');
    el.className = 'result-item result-card';
    el.draggable = true;

    // Drag Start
    el.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', item.id);
        e.dataTransfer.effectAllowed = 'move';
        el.style.opacity = '0.5';
    });
    el.addEventListener('dragend', () => {
        el.style.opacity = '1';
    });

    // Content (Same as previous)
    const desc = item.description || 'No Description';
    el.innerHTML = `
        <div class="mini-card">
            <div class="result-header">
                <span class="part-number">${escapeHtml(item.partNumber)}</span>
                <span class="quantity-badge">${item.quantity}</span>
            </div>
            <div class="result-desc">${escapeHtml(desc)}</div>
             <div style="margin-top:4px; font-size:0.75rem; color:#666;">${escapeHtml(item.location || 'No Loc')}</div>
        </div>
    `;
    return el;
}

function openLabelEditor(item) {
    editItemIdInput.value = item.id;
    // ... Populate other fields ...
    boxEditModal.classList.remove('hidden');
}


// Utils
function escapeHtml(text) {
    if (!text) return '';
    return text.toString().replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

function updateStats() {
    itemCountSpan.textContent = `${inventory.length} items`;
}
