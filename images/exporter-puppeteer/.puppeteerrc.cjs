/**
 * @type {import("puppeteer").Configuration}
 */
module.exports = {
  // Changes the cache location for Puppeteer.
  cacheDirectory: '/app/.cache/puppeteer',
  skipDownload: false,
};