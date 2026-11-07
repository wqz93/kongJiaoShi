// Phase 1 v2: headed browser w/ CDP port, wait for manual login (30min), save state + structure, keep alive
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-core');

const OUT = 'C:/Users/44231/WorkBuddy/SNG/outputs/qsnedu_screenshots';
const LOGIN = 'https://www.qsnedu.com/edumanage/sso/openLogin';
const PORT = 9222;
const STATE_FILE = path.join(OUT, 'auth.json');
const STRUCT_FILE = path.join(OUT, 'after_login_structure.json');
const LOGGED_FLAG = path.join(OUT, 'LOGIN_OK.flag');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  try { fs.unlinkSync(LOGGED_FLAG); } catch {}
  let browser;
  for (const channel of ['msedge', 'chrome']) {
    try {
      browser = await chromium.launch({ channel, headless: false, args: ['--start-maximized', `--remote-debugging-port=${PORT}`] });
      console.log('launched', channel, 'with CDP port', PORT);
      break;
    } catch (e) {}
  }
  if (!browser) { browser = await chromium.launch({ headless: false, args: [`--remote-debugging-port=${PORT}`] }); }
  const ctx = await browser.newContext({ viewport: null });
  const page = await ctx.newPage();
  await page.goto(LOGIN, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(e => console.log('goto warn:', e.message));
  console.log('READY: browser open at login page. Please log in now (max 30 min).');

  const deadline = Date.now() + 30 * 60 * 1000;
  let loggedIn = false;
  let saved = false;
  while (Date.now() < deadline) {
    await page.waitForTimeout(2000);
    try {
      const url = page.url();
      const bodyText = await page.evaluate(() => document.body ? document.body.innerText : '').catch(() => '');
      const loginFormGone = !/立刻登录|忘记密码\?/.test(bodyText);
      const tokenInStorage = await page.evaluate(() => {
        try {
          for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (/token|auth|session|ticket/i.test(k) && String(localStorage.getItem(k)).length > 5) return true; }
          for (let i = 0; i < sessionStorage.length; i++) { const k = sessionStorage.key(i); if (/token|auth|session|ticket/i.test(k) && String(sessionStorage.getItem(k)).length > 5) return true; }
        } catch (e) {}
        return false;
      });
      const tokenInCookie = await page.evaluate(() => /token|auth|ticket|session/i.test(document.cookie));
      if (!/openLogin/i.test(url) || loginFormGone || tokenInStorage || tokenInCookie) {
        if (!loggedIn) console.log('LOGIN DETECTED at', url, { loginFormGone, tokenInStorage, tokenInCookie });
        loggedIn = true;
        // continuously save state
        await ctx.storageState({ path: STATE_FILE }).catch(() => {});
        if (!saved) {
          saved = true;
          fs.writeFileSync(LOGGED_FLAG, new Date().toISOString());
          await page.waitForTimeout(3000);
          await page.screenshot({ path: path.join(OUT, 'after_login_home.png') }).catch(() => {});
          const info = await page.evaluate(() => {
            const links = Array.from(document.querySelectorAll('a[href]')).map(a => ({ text: (a.innerText || '').trim().slice(0, 50), href: a.href }));
            const menuSel = ['li', '.el-menu-item', '.el-submenu__title', '[class*=menu-item]', '[class*=nav] li', 'aside li', '.sidebar li'];
            let menuLike = [];
            for (const sel of menuSel) { document.querySelectorAll(sel).forEach(el => { const t = (el.innerText || '').trim().split('\n').slice(0, 3).join('|'); if (t && t.length < 60) menuLike.push(t); }); }
            return { url: location.href, title: document.title, links: links.slice(0, 300), menuLike: [...new Set(menuLike)].slice(0, 150) };
          }).catch(() => null);
          if (info) { fs.writeFileSync(STRUCT_FILE, JSON.stringify(info, null, 2)); console.log('STRUCTURE SAVED. Menus:', JSON.stringify(info.menuLike.slice(0, 60))); console.log('Post-login URL:', info.url, '| Title:', info.title, '| Links:', info.links.length); }
        }
      }
    } catch (e) { /* page navigating */ }
  }
  console.log('Phase1 window ended. Browser stays open for CDP reuse.');
  // keep process alive so browser stays open
  setInterval(() => {}, 1 << 30);
})().catch(e => { console.error('FATAL', e); process.exit(1); });
