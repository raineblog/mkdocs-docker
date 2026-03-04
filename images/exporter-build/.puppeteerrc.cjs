/**
 * @type {import("puppeteer").Configuration}
 */
module.exports = {
  // Changes the cache location for Puppeteer.
  cacheDirectory: '/github/home/.cache/puppeteer',
  skipDownload: true,
};
