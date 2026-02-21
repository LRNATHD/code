const EasyEDA_API = {
    baseUrl: "https://easyeda.com/api/products",

    /**
     * Fetches component data from EasyEDA API using the LCSC ID or UUID.
     * @param {string} id - LCSC ID (e.g., C2040) or UUID.
     * @returns {Promise<object>} - The component JSON data.
     */
    async getComponent(id) {
        const url = `${this.baseUrl}/${id}/components`;
        console.log(`[EasyEDA_API] Fetching ${url}`);

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();

            if (!data.success) {
                throw new Error(`API returned failure: ${data.code} - ${JSON.stringify(data.result)}`);
            }

            return data.result;
        } catch (error) {
            console.error("[EasyEDA_API] Error fetching component:", error);
            throw error;
        }
    }
};

// Undo export for browser environment if needed, or stick to global object pattern for Manifest V2 generic scripts
// For V2 background scripts, we can just treat this as a global variable loading in order.
// If we were using modules, we'd export it.
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EasyEDA_API;
}
