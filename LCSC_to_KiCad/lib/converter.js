const Converter = {
    // 1 EasyEDA Unit = 10 mil = 0.254 mm
    SCALE: 0.254,

    convert(json) {
        const symbol = this.generateSymbol(json);
        const footprint = this.generateFootprint(json);

        return {
            symbol: symbol,
            footprint: footprint,
            name: json.title || "Component",
            package: json.packageDetail?.title || "Package"
        };
    },

    toMm(val) {
        return (parseFloat(val) * this.SCALE).toFixed(3);
    },

    toMmXY(x, y, originX, originY) {
        const tx = (parseFloat(x) - originX) * this.SCALE;
        const ty = (parseFloat(y) - originY) * this.SCALE;
        return { x: tx.toFixed(3), y: ty.toFixed(3) };
    },

    // KiCad Rotation (CCW) vs EasyEDA (CW likely)
    toRot(rot) {
        let r = parseFloat(rot) || 0;
        // Map CW to CCW
        r = (360 - r) % 360;
        return r;
    },

    generateSymbol(json) {
        const title = json.title || "Unknown";
        // Sanitize title
        const name = title.replace(/\s+/g, "_");
        const ref = "U";
        const footprintName = json.packageDetail?.title || "";

        const head = json.dataStr?.head || { x: 0, y: 0 };
        const originX = parseFloat(head.x) || 0;
        const originY = parseFloat(head.y) || 0;

        let str = `(kicad_symbol_lib (version 20211014) (generator "easyeda2kicad_js")\n`;
        str += `  (symbol "${name}" (in_bom yes) (on_board yes)\n`;
        str += `    (property "Reference" "${ref}" (id 0) (at 0 7.62 0)\n`;
        str += `      (effects (font (size 1.27 1.27)))\n`;
        str += `    )\n`;
        str += `    (property "Value" "${name}" (id 1) (at 0 -7.62 0)\n`;
        str += `      (effects (font (size 1.27 1.27)))\n`;
        str += `    )\n`;
        str += `    (property "Footprint" "${footprintName}" (id 2) (at 0 0 0)\n`;
        str += `      (effects (font (size 1.27 1.27)) hide)\n`;
        str += `    )\n`;

        str += `    (symbol "${name}_1_1"\n`;

        const shapes = json.dataStr?.shape || [];
        shapes.forEach(shapeStr => {
            if (typeof shapeStr !== 'string') return;

            if (shapeStr.startsWith("P~")) { // Pin
                // P~show~type?~num?~x~y~rot~id~locked^^x~y^^path^^nameLine^^numLine...
                const parts = shapeStr.split("^^");
                const params = parts[0].split("~");

                // params: P, show, type, pinNum(maybe), x, y, rot, id, locked
                const x = params[4];
                const y = params[5];
                const rot = params[6];

                // Name part (parts[3])
                // 1~x~y~rot~TEXT~...
                let pinName = "~";
                if (parts[3]) {
                    const nameParams = parts[3].split("~");
                    if (nameParams.length > 4) pinName = nameParams[4];
                }

                // Number part (parts[4])
                let pinNum = "~";
                if (parts[4]) {
                    const numParams = parts[4].split("~");
                    if (numParams.length > 4) pinNum = numParams[4];
                }

                const pos = this.toMmXY(x, y, originX, originY);

                // Map Orientation
                // EasyEDA 0: right??
                // KiCad 0: right (line goes right from pos)
                // Pin line usually drawn in "path" part.
                // Assuming logic: 0=Right, 90=Down, 180=Left, 270=Up.
                // KiCad 'at' rotation:
                // 0: Right
                // 90: Down
                // 180: Left
                // 270: Up
                // If EasyEDA matches KiCad logic (CW/CCW diff?), we might need adjustment.
                // For pins, let's assume direct mapping first, fix if inverted.
                // EasyEDA Y down. KiCad Y down.

                let kRot = parseFloat(rot);
                // Usually EasyEDA Pin Point is the connection point.
                // The line extends AWAY from the body.
                // If rot=0, line goes left? Right?
                // Let's rely on standard assumption: 0=Right.

                str += `      (pin input line (at ${pos.x} ${pos.y} ${kRot}) (length 2.54)\n`;
                str += `        (name "${pinName}" (effects (font (size 1.27 1.27))))\n`;
                str += `        (number "${pinNum}" (effects (font (size 1.27 1.27))))\n`;
                str += `      )\n`;

            } else if (shapeStr.startsWith("R~")) { // Rect
                // Example: R~285~100~~~230~380...
                // Hypothesized format: R~x~y~?~?~w~h...
                const p = shapeStr.split("~");
                const x = parseFloat(p[1]);
                const y = parseFloat(p[2]);

                // Try to find width/height.
                // If p[3] and p[4] are empty, check p[5] and p[6]
                let w = parseFloat(p[3]);
                let h = parseFloat(p[4]);

                if (isNaN(w)) w = parseFloat(p[5]);
                if (isNaN(h)) h = parseFloat(p[6]);

                if (!isNaN(x) && !isNaN(y) && !isNaN(w) && !isNaN(h)) {
                    const start = this.toMmXY(x, y, originX, originY);
                    const end = this.toMmXY(x + w, y + h, originX, originY);

                    str += `    (rectangle (start ${start.x} ${start.y}) (end ${end.x} ${end.y})\n`;
                    str += `      (stroke (width 0.254) (type default) (color 0 0 0 0))\n`;
                    str += `      (fill (type none))\n`;
                    str += `    )\n`;
                }

            }
        });

        // Ensure at least a rectangle body if none found?
        // KiCad needs a body? No, just pins.

        str += `    )\n`;
        str += `  )\n`;
        str += `)\n`;

        return str;
    },

    generateFootprint(json) {
        const pkg = json.packageDetail;
        const name = pkg?.title || "Unknown_Package";

        const head = pkg?.dataStr?.head || { x: 0, y: 0 };
        const originX = parseFloat(head.x) || 0;
        const originY = parseFloat(head.y) || 0;

        let str = `(footprint "${name}" (layer "F.Cu") (tedit 0)\n`;
        str += `  (attr smd)\n`;

        const shapes = pkg?.dataStr?.shape || [];

        shapes.forEach(shapeStr => {
            if (typeof shapeStr !== 'string') return;
            const p = shapeStr.split("~");
            const type = p[0];

            if (type === "PAD") {
                // PAD~Shape~x~y~w~h~layer~net~num~rot~points
                // Shape: RECT, OVAL, ELLIPSE, POLYGON?
                const shape = p[1];
                const x = p[2];
                const y = p[3];
                const w = p[4];
                const h = p[5];
                const layerId = p[6];
                // const net = p[7];
                const num = p[8];
                const rot = p[9];

                const pos = this.toMmXY(x, y, originX, originY);
                const sizeW = this.toMm(w);
                const sizeH = this.toMm(h);
                const kRot = this.toRot(rot);

                let kShape = "rect";
                if (shape === "OVAL" || shape === "ELLIPSE") kShape = "oval";
                if (shape === "CIRCLE") kShape = "circle"; // Valid?

                // Layer mapping
                // EasyEDA: 1=Top, 2=Bottom, 11=Multi
                let kLayers = '"F.Cu" "F.Paste" "F.Mask"';
                if (layerId === "2") kLayers = '"B.Cu" "B.Paste" "B.Mask"';
                if (layerId === "11") kLayers = '"*.Cu" "F.Mask" "B.Mask"'; // Through hole?

                // Type: Check layer 11 -> Through Hole?
                let padType = "smd";
                if (layerId === "11") {
                    padType = "thru_hole";
                    kShape = "circle"; // Default loop
                    // If Multi-layer, usually we have hole size?
                    // EasyEDA PAD format has hole info?
                    // "PAD~ELLIPSE~...~holeD" ??
                    // Standard PAD string length is dynamic.
                    // If hole exists, it's usually later.
                    // For now, assume SMD for safety if not sure.
                }

                str += `  (pad "${num}" ${padType} ${kShape} (at ${pos.x} ${pos.y} ${kRot}) (size ${sizeW} ${sizeH}) (layers ${kLayers}))\n`;

            } else if (type === "TRACK") {
                // TRACK~width~layer~net~points...
            } else if (type === "SOLIDREGION") {
                // SOLIDREGION~layer~net~pathStr~type...
            } else if (type === "CIRCLE") {
                // CIRCLE~cx~cy~radius~width~layer...
                const cx = p[1];
                const cy = p[2];
                const r = p[3];
                // const w = p[4];
                const layer = p[5];

                // Only draw silk?
                if (layer === "3" || layer === "4" || layer === "1") { // 3=TopSilk
                    const pos = this.toMmXY(cx, cy, originX, originY);
                    // KiCad circle: (fp_circle (center 0 0) (end 1.5 0) (layer "F.SilkS") (width 0.12))
                    // End point? Center + radius.
                    const radMm = parseFloat(this.toMm(r));
                    const endX = (parseFloat(pos.x) + radMm).toFixed(3);

                    let kLayer = "F.SilkS";
                    if (layer === "4") kLayer = "B.SilkS";

                    str += `  (fp_circle (center ${pos.x} ${pos.y}) (end ${endX} ${pos.y}) (layer "${kLayer}") (width 0.12))\n`;
                }
            }
        });

        str += `)\n`;
        return str;
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = Converter;
}
