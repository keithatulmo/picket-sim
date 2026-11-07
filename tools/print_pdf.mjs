// Print a local HTML file to PDF with Chromium (Playwright). Usage:
//   node tools/print_pdf.mjs <input.html> <output.pdf> "<footer label>"
import { createRequire } from 'module';
import path from 'path';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const [, , input, output, label = ''] = process.argv;
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto('file://' + path.resolve(input), { waitUntil: 'load' });
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
await page.pdf({
  path: output,
  format: 'Letter',
  printBackground: true,
  margin: { top: '0.65in', bottom: '0.7in', left: '0.6in', right: '0.6in' },
  displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate:
    `<div style="font-size:7px;width:100%;padding:0 0.6in;color:#52514e;display:flex;justify-content:space-between;">` +
    `<span>${esc(label)}</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>`,
});
await browser.close();
