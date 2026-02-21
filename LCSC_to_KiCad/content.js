console.log("LCSC to KiCad: Content script loaded.");

function getProductCode() {
    // Strategy 1: URL
    const urlMatch = window.location.href.match(/product-detail\/.*_(C\d+)/);
    if (urlMatch) return urlMatch[1];

    // Strategy 2: DOM
    const domMatch = document.body.innerText.match(/Product Code:\s*(C\d+)/);
    if (domMatch) return domMatch[1];

    // Strategy 3: Table cell
    const cells = document.querySelectorAll('td');
    for (const cell of cells) {
        if (cell.innerText.trim() === 'LCSC Part #') {
            const next = cell.nextElementSibling;
            if (next) return next.innerText.trim();
        }
    }

    return null;
}

function triggerDownload() {
    const productCode = getProductCode();
    if (productCode) {
        console.log("LCSC to KiCad: requesting download for " + productCode);
        browser.runtime.sendMessage({
            action: "download_component",
            productCode: productCode
        });
    } else {
        alert("Could not find Product Code (Cxxxx) on this page.");
    }
}

// Function to inject button
function injectButton() {
    if (document.getElementById('lcsc2kicad-btn')) return;

    // Find the target element
    // Strategy: Find any button with text "Add to Cart"
    const buttons = document.querySelectorAll('button, a, div[role="button"]');
    let target = null;

    for (const btn of buttons) {
        if (btn.innerText && btn.innerText.toLowerCase().includes('add to cart')) {
            target = btn;
            break;
        }
    }

    // Fallback: .cart-add-btn
    if (!target) {
        target = document.querySelector('.cart-add-btn') || document.querySelector('.add-to-cart');
    }

    if (target) {
        console.log("Found injection target:", target);
        const btn = document.createElement('button');
        btn.id = 'lcsc2kicad-btn';
        btn.innerText = 'Download to KiCad';
        btn.style.marginLeft = '10px';
        btn.style.backgroundColor = '#4CAF50';
        btn.style.color = 'white';
        btn.style.border = 'none';
        btn.style.padding = '5px 10px'; // Slightly smaller to fit better
        btn.style.cursor = 'pointer';
        btn.style.fontSize = '14px';
        btn.style.fontWeight = 'bold';
        btn.style.borderRadius = '4px';
        btn.style.zIndex = '9999';

        btn.onclick = function (e) {
            e.preventDefault();
            e.stopPropagation();
            triggerDownload();
        };

        // Insert after the target
        target.parentNode.insertBefore(btn, target.nextSibling);
    }
}

// Listen for messages from context menu
browser.runtime.onMessage.addListener((message) => {
    if (message.action === "trigger_download") {
        triggerDownload();
    }
});

// Run injection with Observer
const observer = new MutationObserver((mutations) => {
    injectButton();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Initial try
setTimeout(injectButton, 1000);
setTimeout(injectButton, 3000);
setTimeout(injectButton, 5000); // multiple checks for slow loads
