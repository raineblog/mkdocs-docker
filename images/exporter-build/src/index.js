const puppeteer = require('puppeteer');
const http = require('http');
const fs = require('fs');
const path = require('path');
const mime = require('mime-types');

// Simple high-performance static file server
function startLocalServer(baseDir, port) {
    return new Promise((resolve, reject) => {
        const server = http.createServer((req, res) => {
            let reqUrl = decodeURI(req.url.split('?')[0]);
            if (reqUrl.endsWith('/')) {
                reqUrl += 'index.html';
            }
            const filePath = path.join(baseDir, reqUrl);
            if (!filePath.startsWith(baseDir)) {
                res.statusCode = 403;
                res.end('Forbidden');
                return;
            }
            fs.readFile(filePath, (err, data) => {
                if (err) {
                    res.statusCode = 404;
                    res.end(`File not found: ${reqUrl}`);
                    return;
                }
                const contentType = mime.contentType(path.extname(filePath)) || 'application/octet-stream';
                res.setHeader('Content-Type', contentType);
                res.writeHead(200);
                res.end(data);
            });
        });
        server.on('error', (e) => reject(e));
        server.listen(port, '127.0.0.1', () => {
            console.log(`[HTTP Server] Serving ${baseDir} on http://127.0.0.1:${port}`);
            resolve(server);
        });
    });
}

// Concurrency queue
async function processTasks(tasks, port, maxConcurrent) {
    console.log(`[Puppeteer] Starting conversion... Total: ${tasks.length}, Concurrency: ${maxConcurrent}`);

    const browser = await puppeteer.launch({
        executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || null,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--font-render-hinting=none',
        ]
    });

    let index = 0;
    let completed = 0;
    let failed = 0;

    async function worker(workerId) {
        const context = await browser.createBrowserContext();
        const page = await context.newPage();

        while (true) {
            let taskIndex;
            if (index < tasks.length) {
                taskIndex = index++;
            } else {
                break;
            }

            const task = tasks[taskIndex];
            let reqPath = task.url;
            if (reqPath.startsWith('./site/')) reqPath = reqPath.replace('./site/', '/');
            else if (reqPath.startsWith('site/')) reqPath = reqPath.replace('site/', '/');
            else if (!reqPath.startsWith('/')) reqPath = '/' + reqPath;

            const fullUrl = `http://127.0.0.1:${port}${reqPath}`;
            const pdfDest = path.join(process.cwd(), 'site', 'build', task.pdf_path);

            console.log(`[Worker ${workerId}] [${completed + 1}/${tasks.length}] Fetching ${fullUrl} -> ${task.pdf_path}`);

            try {
                fs.mkdirSync(path.dirname(pdfDest), { recursive: true });

                await page.goto(fullUrl, { waitUntil: 'load', timeout: 60000 });
                await page.evaluateHandle('document.fonts.ready');

                // Important: outline: true generates initial PDF bookmarks from H1-H6
                await page.pdf({
                    path: pdfDest,
                    waitForFonts: true,
                    format: 'A4',
                    printBackground: true,
                    displayHeaderFooter: false,
                    omitBackground: true,
                    outline: true, 
                    margin: {
                        top: '2.54cm',
                        bottom: '2.54cm',
                        left: '1.91cm',
                        right: '1.91cm'
                    }
                });

                completed++;
            } catch (err) {
                console.error(`[Worker ${workerId}] Error rendering ${fullUrl}:`, err.message);
                failed++;
            }
        }
        await page.close();
        await context.close();
    }

    const workers = [];
    for (let i = 0; i < maxConcurrent; i++) {
        workers.push(worker(i));
    }

    await Promise.all(workers);
    await browser.close();

    console.log(`[Puppeteer] Converted: ${completed}, Failed: ${failed}`);
    if (failed > 0) {
        process.exit(1);
    }
}

async function main() {
    const bookName = process.argv[2];
    if (!bookName) {
        console.error("Usage: node index.js <book-name>");
        process.exit(1);
    }

    const buildDir = path.join(process.cwd(), 'site', 'build');
    const siteDir = path.join(process.cwd(), 'site');
    const tasksFile = path.join(buildDir, `download_${bookName}.json`);

    if (!fs.existsSync(tasksFile)) {
        console.error(`Tasks file not found at ${tasksFile}. Exiting.`);
        process.exit(1);
    }

    const tasks = JSON.parse(fs.readFileSync(tasksFile, 'utf-8'));
    if (!tasks || tasks.length === 0) {
        console.log("No tasks found. Exiting.");
        return;
    }

    const PORT = 3000;
    const server = await startLocalServer(siteDir, PORT);
    const maxConcurrent = parseInt(process.env.CONCURRENCY) || 4;

    try {
        await processTasks(tasks, PORT, maxConcurrent);
    } catch (e) {
        console.error("Critical error during processing:", e);
        process.exit(1);
    } finally {
        server.close();
    }
}

main();
