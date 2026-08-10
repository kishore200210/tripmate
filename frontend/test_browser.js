const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  // Intercept requests to see what is sent
  await page.setRequestInterception(true);
  page.on('request', interceptedRequest => {
    if (interceptedRequest.url().includes('/auth/register')) {
      console.log("SENDING REQUEST TO:", interceptedRequest.url());
      console.log("PAYLOAD:", interceptedRequest.postData());
    }
    interceptedRequest.continue();
  });

  page.on('response', async response => {
    if (response.url().includes('/auth/register')) {
      console.log("RESPONSE STATUS:", response.status());
      try {
        console.log("RESPONSE BODY:", await response.text());
      } catch (e) {}
    }
  });

  await page.goto('http://localhost:3000/signup');
  
  // Fill form
  await page.type('#name', 'Test User');
  await page.type('#email', 'test3@example.com');
  await page.type('#password', 'Password123!');
  
  // Click submit
  await page.click('button[type="submit"]');
  
  // Wait a bit for the request
  await new Promise(r => setTimeout(r, 2000));
  
  await browser.close();
})();
