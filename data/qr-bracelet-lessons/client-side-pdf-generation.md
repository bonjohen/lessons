---
title: "Client-Side PDF Generation in Serverless"
summary: "When your serverless backend can't run PDF libraries (no headless Chrome, no native modules), generate the PDF in the browser instead. The server renders an HTML page with the data embedded, and client-side JavaScript builds and downloads the PDF. The user doesn't notice the difference."
date: 2026-06-06
lesson_type: implementation
tags: [cloudflare, serverless, pdf, frontend, javascript]
---
# Client-Side PDF Generation in Serverless

## The Lesson

When your serverless backend can't run PDF libraries (no headless Chrome, no native modules), generate the PDF in the browser instead. The server renders an HTML page with the data embedded, and client-side JavaScript builds and downloads the PDF. The user doesn't notice the difference.

## Context

MyReachBand generates printable bracelet sheets — 8 strips per 8.5"x11" page, each with a QR code, band text, and a URL. Cloudflare Workers can't run headless Chrome (paid add-on) or Node.js PDF libraries like `pdfkit` (native dependencies). The solution: the Worker serves an HTML page that loads jsPDF and qrcode-generator from CDNs, generates the PDF client-side, and triggers a download.

## What Happened

1. Explored server-side options: Cloudflare Browser Rendering (paid), pdf-lib (limited text/layout support), raw PDF byte generation (complex). None were practical for a free-tier project.
2. Chose client-side generation with jsPDF (handles PDF creation, text, images) and qrcode-generator (creates QR as SVG, converted to PNG via canvas).
3. The Worker serves a page at `/bracelets/:id/print` with the bracelet's share URL and band text embedded in the HTML.
4. JavaScript on the page generates the QR code, builds the PDF with precise dimensions (inches, not pixels), and triggers `doc.save()` which downloads the file.
5. Iterated on layout: dotted cut lines (jsPDF's `setLineDashPattern` renders as blocks — had to draw dots manually), vertical text positioning, and font sizing.
6. Used `doc.getTextWidth()` to measure text for centering, and discovered that jsPDF's `angle` parameter for rotated text rotates around the text origin, requiring manual offset calculation.

## Key Insights

- **jsPDF works in inches.** `new jsPDF({unit:'in',format:'letter'})` gives you an 8.5x11 coordinate system. No DPI math needed — `doc.addImage(img, 'PNG', 1, 1, 2, 2)` places a 2"x2" image at position (1,1).
- **QR codes: generate as SVG, convert to PNG via canvas.** qrcode-generator creates SVGs. Render the SVG to a canvas, export as `canvas.toDataURL('image/png')`, then pass to `doc.addImage()`.
- **jsPDF's dash patterns don't work reliably.** `setLineDashPattern` renders as solid blocks in many PDF viewers. Draw dotted lines manually with a loop of tiny `doc.line()` segments.
- **Rotated text positioning is non-intuitive.** `doc.text('hello', x, y, {angle: 90})` rotates around (x, y). For vertical text centered in a space, use `doc.getTextWidth()` to measure and offset manually.
- **CDN loading is fine for tools.** Loading jsPDF (90KB) and qrcode-generator (15KB) from CDNs adds ~100ms on first load. The user clicks a button, waits ~500ms, gets a PDF. Perfectly acceptable.
- **Keep data in the HTML, logic in the script.** The Worker embeds the share URL and band text as JavaScript variables in the page. The PDF generation script reads them — no API calls needed from the client.

## Examples

### Loading libraries from CDN
```html
<script src="https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.min.js"></script>
```

### Generating a QR code as PNG data URL
```javascript
var qr = qrcode(0, 'H');
qr.addData('https://myreachband.com/b/ABC123?t=token');
qr.make();
var svg = qr.createSvgTag({cellSize: 8, margin: 0});
var blob = new Blob([svg], {type: 'image/svg+xml'});
var img = new Image();
img.onload = function() {
  var canvas = document.createElement('canvas');
  canvas.width = 400; canvas.height = 400;
  canvas.getContext('2d').drawImage(img, 0, 0, 400, 400);
  var pngDataUrl = canvas.toDataURL('image/png');
  // Use pngDataUrl with jsPDF
};
img.src = URL.createObjectURL(blob);
```

### Drawing dotted lines (workaround)
```javascript
function drawDottedLine(doc, x1, y1, x2, y2) {
  doc.setDrawColor(180, 180, 180);
  doc.setLineWidth(0.01);
  for (var x = x1; x < x2; x += 0.1) {
    doc.line(x, y1, Math.min(x + 0.02, x2), y2);
  }
}
```

## Applicability

Client-side PDF generation works whenever the data is already available in the browser and the layout is programmatic (not complex typesetting). Good for: invoices, tickets, labels, reports, certificates. NOT good for: PDFs that require server-only data, or complex layouts with flowing text, tables, and images (use a server-side tool for those).

## Related Lessons

- [Cloudflare Workers](cloudflare-workers.md) — the serverless constraint that drove client-side generation
