// Crawl qsnedu.com public pages and screenshot each unique page
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright-core');

const OUT = 'C:/Users/44231/WorkBuddy/SNG/outputs/qsnedu_screenshots';
const START = 'https://www.qsnedu.com/edumanage/sso/openLogin';
const SEEDS = [
  'https://www.qsnedu.com/edumanage/sso/openLogin',
  'https://www.qsnedu.com/',
  'https://www.qsnedu.com/portal',
  'https://www.qsnedu.com/home',
  'https://www.qsnedu.com/index.html',
  'https://www.qsnedu.com/edumanage/',
  'https://www.qsnedu.com/edumanage/sso/login',
  'https://www.qsnedu.com/edumanage/register',
  'https://www.qsnedu.com/edumanage/sso/register',
  'https://www.qsnedu.com/portal/',
  'https://www.qsnedu.com/web/',
  'https://www.qsnedu.com/h5/',
  'https://www.qsnedu.com/mobile/',
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const manifest = [];
  const results = [];

  let browser;
  for (const channel of ['msedge', 'chrome']) {
    try { browser = await chromium.launch({ channel, headless: true }); console.log('launched', channel); break; } catch (e) {}
  }
  if (!browser) { try { browser = await chromium.launch({ headless: true }); console.log('launched bundled chromium'); } catch (e) { console.error('no browser', e.message); process.exit(1); } }

  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  const visited = new Set();
  const queue = SEEDS.map(u => ({ url: u, source: 'seed' }));
  let idx = 0;

  const norm = u => { try { const x = new URL(u); return x.origin + x.pathname.replace(/\/+$/, ''); } catch { return null; } };

  while (queue.length && idx < 40) {
    const { url } = queue.shift();
    const key = norm(url);
    if (!key || visited.has(key)) continue;
    visited.add(key);
    idx++;
    try {
      const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForTimeout(1500); // let SPA render
      const status = resp ? resp.status() : 0;
      const finalUrl = page.url();
      const title = (await page.title().catch(() => '')) || '';
      const bodyText = await page.evaluate(() => document.body ? document.body.innerText.slice(0, 200) : '');
      const isErr = status >= 400 || /502|503|404|Bad Gateway|无法访问/i.test(bodyText);

      if (!isErr) {
        const fname = `${String(idx).padStart(2, '0')}_${norm(finalUrl).replace(/[^a-zA-Z0-9]+/g, '_').slice(0, 60)}.png`;
        await page.screenshot({ path: path.join(OUT, fname), fullPage: true });
        results.push({ url: finalUrl, status, title, file: fname, snippet: bodyText.replace(/\s+/g, ' ').slice(0, 80) });
        console.log(`OK  [${status}] ${finalUrl}  "${title}" -> ${fname}`);
        // collect same-origin links
        const links = await page.evaluate(() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href));
        for (const l of links) {
          try { const u2 = new URL(l); if (u2.hostname === 'www.qsnedu.com' && !visited.has(norm(l))) queue.push({ url: l, source: 'crawl' }); } catch {}
        }
      } else {
        console.log(`ERR [${status}] ${url} :: ${bodyText.replace(/\s+/g, ' ').slice(0, 60)}`);
      }
    } catch (e) {
      console.log(`FAIL ${url} :: ${String(e.message).slice(0, 80)}`);
    }
  }

  fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(results, null, 2));
  console.log(`\nDone. ${results.length} pages captured -> ${OUT}`);
  await browser.close();
})();
