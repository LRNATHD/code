console.log("LCSC to KiCad: Background script loaded.");

browser.runtime.onInstalled.addListener(() => {
    browser.contextMenus.create({
        id: "download-kicad",
        title: "Download to KiCad",
        contexts: ["page"],
        documentUrlPatterns: ["*://lcsc.com/product-detail/*", "*://www.lcsc.com/product-detail/*"]
    });
});

browser.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "download-kicad") {
        browser.tabs.sendMessage(tab.id, { action: "trigger_download" });
    }
});


browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "download_component") {
        const id = message.productCode;
        console.log("Processing download for: " + id);

        // Use the EasyEDA_API (global from lib/easyeda_api.js)
        EasyEDA_API.getComponent(id)
            .then(json => {
                console.log("Fetched JSON for " + id);

                // Convert
                const kicadData = Converter.convert(json); // Global from lib/converter.js

                // Define Filenames
                // Use symbol name or LCSC ID? LCSC ID + Name is good.
                const safeName = kicadData.name.replace(/[^a-zA-Z0-9_-]/g, "_");
                const filenameBase = `${id}_${safeName}`;

                // Get user preference for path
                browser.storage.local.get("downloadPath").then(res => {
                    const downloadDir = res.downloadPath || "KiCad_Imports";

                    // Save Symbol
                    const symbolBlob = new Blob([kicadData.symbol], { type: "text/plain" });
                    const symbolUrl = URL.createObjectURL(symbolBlob);

                    browser.downloads.download({
                        url: symbolUrl,
                        filename: `${downloadDir}/${filenameBase}.kicad_sym`,
                        saveAs: false,
                        conflictAction: 'overwrite'
                    });

                    // Save Footprint
                    const fpBlob = new Blob([kicadData.footprint], { type: "text/plain" });
                    const fpUrl = URL.createObjectURL(fpBlob);

                    browser.downloads.download({
                        url: fpUrl,
                        filename: `${downloadDir}/${filenameBase}.kicad_mod`,
                        saveAs: false,
                        conflictAction: 'overwrite'
                    });

                    console.log(`Downloads initiated to ${downloadDir}/`);
                });
            })
            .catch(err => {
                console.error("Error processing download:", err);
                // Optionally notify content script to show alert
                // browser.tabs.sendMessage(sender.tab.id, { action: "error", message: err.toString() });
            });
    }
});
