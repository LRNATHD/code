# PartScout - Electronic Component Inventory

A local web application to track components ordered from DigiKey, LCSC, and other suppliers.

## Features
- **Search**: Instantly find if you've ordered a part by searching for its name or specifications (e.g., "330nF", "STM32").
- **Import**: Upload CSV order history files directly from LCSC or DigiKey.
- **Privacy**: All data is stored locally in your browser (LocalStorage). Nothing is uploaded to the cloud.

## How to Use
1. **Open the App**: Double-click `index.html` to open it in your web browser.
2. **Import Data**: 
   - Export your order history as CSV from your supplier.
   - Click "Import Order CSV" in the app and select the file.
   - The app will parse standard columns (Part #, Description, Qty).
3. **Search**: Type in the search bar. Results appear instantly.

## Tech Stack
- HTML5
- Vanilla CSS (Glassmorphism, Dark Mode)
- Vanilla JavaScript (No build step required)
