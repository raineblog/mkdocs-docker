import path from 'path';
import fs from 'fs';

import { defineConfig } from '@rspress/core';
import { pluginRss } from '@rspress/plugin-rss';
import { pluginSitemap } from '@rspress/plugin-sitemap';

import remarkGfm from 'remark-gfm';
import remarkCjkFriendly from "remark-cjk-friendly";

import remarkEmoji from 'remark-emoji';
import readingTime from 'rspress-plugin-reading-time';

// 导入重构后的工具模块
import { remarkKatexPlugins, rehypeKatexPlugins } from './utils/katex';
import { parseNavAndSidebar } from './utils/sidebar';
import { mapSocialLinks } from './utils/social';

// 读取配置文件
const readConfig = (name: string) => {
  const filePath = path.join(__dirname, 'config', `${name}.json`);
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
};

const projectConfig = readConfig('project');
const navConfig = readConfig('nav');
const extraConfig = readConfig('extra');

// 获取并校验 site_url 环境变量
const siteUrl = process.env.site_url;
if (!siteUrl) {
  throw new Error('site_url environment variable is required');
}

let base = '/';
try {
  const url = new URL(siteUrl);
  base = url.pathname;
  if (!base.endsWith('/')) {
    base += '/';
  }
} catch (e) {
  throw new Error(`Invalid site_url: "${siteUrl}". It must be a valid absolute URL (e.g., https://example.com/ or https://example.com/docs).`);
}

const { nav, sidebar } = parseNavAndSidebar(navConfig);

export default defineConfig({
  root: path.join(__dirname, 'docs'),
  base: base,
  title: projectConfig.info.site_name,
  description: projectConfig.info.site_description,
  lang: 'zh',
  logoText: projectConfig.info.site_name,
  icon: `./docs/${projectConfig.theme.favicon}`,
  logo: `/${projectConfig.theme.logo}`,
  llms: true,
  globalStyles: path.join(__dirname, 'styles/custom.css'),
  markdown: {
    showLineNumbers: true,
    shiki: {
      defaultLanguage: 'text',
      fallbackLanguage: 'text'
    },
    remarkPlugins: [
      ...remarkKatexPlugins,
      remarkGfm,
      remarkCjkFriendly,
      remarkEmoji
    ] as any,
    rehypePlugins: [
      ...rehypeKatexPlugins
    ] as any,
  },
  themeConfig: {
    nav: nav,
    sidebar: sidebar,
    llmsUI: false,
    enableContentAnimation: true,
    enableAppearanceAnimation: true,
    enableScrollToTop: true,
    footer: {
      message: projectConfig.info.copyright,
    },
    socialLinks: mapSocialLinks(extraConfig.social),
    editLink: {
      docRepoBaseUrl: `${projectConfig.info.repo_url}/blob/main/docs/`,
    },
  },
  plugins: [
    readingTime({
      defaultLocale: 'zh-CN',
    }),
    pluginRss({
      siteUrl: siteUrl,
      feed: {
        id: 'blog',
        test: '/blog/',
        item: (item: any, page: any) => {
          if (!item.date) {
            // 尝试从路径中匹配日期 (例如 2026-01-26)
            const dateMatch = page.routePath.match(/(\d{4}-\d{2}-\d{2})/);
            if (dateMatch) {
              item.date = new Date(dateMatch[1]);
            } else {
              // 如果无法匹配，默认使用当前时间，避免 toISOString() 报错
              item.date = new Date();
            }
          }
          return item;
        },
      },
    }),
    pluginSitemap({
      siteUrl: siteUrl,
    }),
  ],
});
