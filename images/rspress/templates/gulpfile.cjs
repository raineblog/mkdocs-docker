const gulp = require('gulp');
const cheerio = require('gulp-cheerio');

// 你的 Rspress 编译输出目录（默认为 doc_build）
const BUILD_DIR = 'doc_build';

// 定义一个名为 process-images 的任务
gulp.task('process-images', () => {
  console.log(`\n🚀 开始二次处理 ${BUILD_DIR} 目录下的 HTML 图片...`);
  
  // 匹配输出目录下所有的 .html 文件
  return gulp.src(`${BUILD_DIR}/**/*.html`)
    .pipe(cheerio({
      run: ($, file) => {
        let hasModified = false;

        // 遍历当前 HTML 文件中的所有 <img> 标签
        $('img').each(function () {
          const img = $(this);
          const altText = img.attr('alt');

          // 如果没有 alt 或者不包含 | 符号，直接跳过
          if (!altText || !altText.includes('|')) return;

          const parts = altText.split('|');
          const realAltParts = [];
          
          // 获取图片现有的 style（如果有的话），并准备追加
          let style = img.attr('style') || '';
          if (style && !style.trim().endsWith(';')) style += '; ';

          // 核心解析逻辑（与之前的 Remark/JS 版本完全一致）
          for (let i = 0; i < parts.length; i++) {
            const part = parts[i].trim();
            const lowerPart = part.toLowerCase();

            // 第一部分永远是真实的 alt 文本
            if (i === 0) {
              realAltParts.push(part);
              continue;
            }

            // 解析对齐
            if (lowerPart === 'left') {
              style += 'float: left; margin-right: 1.5rem; ';
              continue;
            }
            if (lowerPart === 'right') {
              style += 'float: right; margin-left: 1.5rem; ';
              continue;
            }
            if (lowerPart === 'center') {
              style += 'display: block; margin-left: auto; margin-right: auto; ';
              continue;
            }

            // 解析宽度
            const widthMatch = lowerPart.match(/^w(\d+(?:\.\d+)?)([a-z%]*)$/);
            if (widthMatch) {
              style += `width: ${widthMatch[1]}${widthMatch[2] || '%'}; `;
              continue;
            }

            // 解析高度
            const heightMatch = lowerPart.match(/^h(\d+(?:\.\d+)?)([a-z%]*)$/);
            if (heightMatch) {
              style += `height: ${heightMatch[1]}${heightMatch[2] || 'px'}; `;
              continue;
            }

            // 如果都不是，说明它是原生 alt 描述里误伤的 |
            realAltParts.push(part);
          }

          // 如果我们成功生成了样式，就更新 DOM
          if (style !== img.attr('style')) {
            img.attr('style', style.trim());
            // 还原干净的 alt 属性
            img.attr('alt', realAltParts.join(' | ').trim());
            hasModified = true;
          }
        });

        // 打印处理日志（可选，让你知道改了哪些文件）
        if (hasModified) {
          console.log(`✅ 已处理: ${file.relative}`);
        }
      },
      // 保持原有 HTML 格式，不要把文件压缩成一行
      parserOptions: {
        decodeEntities: false, 
        lowerCaseTags: false
      }
    }))
    // 将修改后的 HTML 覆盖写回原目录
    .pipe(gulp.dest(BUILD_DIR));
});

// 默认任务
gulp.task('default', gulp.series('process-images'));