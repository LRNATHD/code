const fs = require('fs');
const Converter = require('./lib/converter.js');

try {
    const jsonStr = fs.readFileSync('./easyeda_c2040.json', 'utf8');
    const json = JSON.parse(jsonStr);

    console.log("Loaded JSON. Testing conversion...");
    const result = Converter.convert(json);

    console.log("--- SYMBOL ---");
    console.log(result.symbol);
    console.log("--- FOOTPRINT ---");
    console.log(result.footprint);

    // Validate output (basic check)
    if (result.symbol.includes("(pin") && result.footprint.includes("(pad")) {
        console.log("SUCCESS: Output contains pins and pads.");
    } else {
        console.log("WARNING: Output seems incomplete.");
    }

} catch (e) {
    console.error("Test Failed:", e);
}
