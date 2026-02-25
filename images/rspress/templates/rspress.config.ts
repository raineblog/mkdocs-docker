import path from 'path';
import fs from 'fs';

import { defineConfig } from '@rspress/core';
import { pluginRss } from '@rspress/plugin-rss';
import { pluginSitemap } from '@rspress/plugin-sitemap';

import remarkGfm from 'remark-gfm';
import remarkCjkFriendly from "remark-cjk-friendly";

import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// @ts-ignore
import remarkImageAttributes from 'remark-image-attributes'

import remarkEmoji from 'remark-emoji';
import readingTime from 'rspress-plugin-reading-time';

function localKatexPlugin() {
  return {
    name: 'local-katex-plugin',
    markdown: {
      remarkPlugins: [remarkMath] as any,
      rehypePlugins: [
        [rehypeKatex as any, {
          trust: true,
          throwOnError: false,
          strict: false,
          macros: {
            "\\RR": "\\mathbb{R}",
            "\\i": "\\mathrm{i}",
            "\\d": "\\mathrm{d}",
            "\\C": "\\mathbb{C}",
            "\\R": "\\mathbb{R}",
            "\\Q": "\\mathbb{Q}",
            "\\Z": "\\mathbb{Z}",
            "\\N": "\\mathbb{N}",
            "\\P": "\\mathbb{P}",
            "\\degree": "^\\circ",
            "\\rank": "\\operatorname{rank}",
            "\\op": "\\operatorname",
            "\\paren": "\\left({#1}\\right)",
            "\\bracket": "\\left[{#1}\\right]",
            "\\brace": "\\left\\{{#1}\\right\\}",
            "\\ceil": "\\left\\lceil{#1}\\right\\rceil",
            "\\floor": "\\left\\lfloor{#1}\\right\\rfloor",
            "\\vert": "\\left\\lvert{#1}\\right\\rvert",
            "\\vec": "\\bm",
            "\\vecc": "\\overrightarrow",
            "\\poly": "\\ce{-\\!\\!\\![ #1 ]_n\\!\\!\\!\\!\\!-}",
            "\\el": "#1\\mathrm{#2}^{#3}",
            "\\pH": "p\\ce{H}",
            "\\pOH": "p\\ce{OH}",
            "\\con": "\\left[\\ce{#1}\\right]",
            "’": "'",
            "，": ",",
            "。": ".",
            "；": ";",
            "：": ":",
            "！": "!",
            "？": "?",
            "【": "[",
            "】": "]",
            "（": "(",
            "）": ")",
            "、": ",",
            "—": "-",
            "…": "\\dots",
            "·": "\\cdot",
            "->": "\\to",
            "<-": "\\gets"
          }
        }]
      ] as any,
    }
  };
}

// 图片解析

import { visit } from 'unist-util-visit';
import type { Plugin } from 'unified';

const remarkCodeBlockToMath: Plugin = () => {
  return (tree) => {
    visit(tree, 'image', (node: any) => {
      // 1. 如果没有 alt，或者 alt 里完全没有 |，则跳过处理
      if (!node.alt || !node.alt.includes('|')) return;

      // 2. 用 | 分割整个 alt 字符串
      const parts = node.alt.split('|');
      
      // 存储真实的 alt 文本片段
      const realAltParts = [];
      let style = '';

      // 3. 遍历分割出来的所有部分
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i].trim();
        const lowerPart = part.toLowerCase();

        // 第一部分永远是 alt 文本（即便是空的）
        if (i === 0) {
          realAltParts.push(part);
          continue;
        }

        // --- 匹配对齐方式 ---
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

        // --- 匹配宽度 (以 w 开头 + 数字 + 可选的单位) ---
        const widthMatch = lowerPart.match(/^w(\d+(?:\.\d+)?)([a-z%]*)$/);
        if (widthMatch) {
          const num = widthMatch[1];     // 提取数字，例如 "80"
          const unit = widthMatch[2];    // 提取单位，例如 "%", "px"
          // 如果只有数字没给单位，宽度默认使用 "%"
          const finalUnit = unit || '%'; 
          style += `width: ${num}${finalUnit}; `;
          continue;
        }

        // --- 匹配高度 (以 h 开头 + 数字 + 可选的单位) ---
        const heightMatch = lowerPart.match(/^h(\d+(?:\.\d+)?)([a-z%]*)$/);
        if (heightMatch) {
          const num = heightMatch[1];
          const unit = heightMatch[2];
          // 如果只有数字没给单位，高度默认使用 "px" (因为高度用 % 往往在网页中无效)
          const finalUnit = unit || 'px'; 
          style += `height: ${num}${finalUnit}; `;
          continue;
        }

        // --- 如果都不是，说明它是原始 alt 描述里本来就带有的 | 符号 ---
        // 我们把它放回真实 alt 数组中
        realAltParts.push(part);
      }

      // 4. 还原干净的 alt 属性给节点 (拼接回去)
      // 如果原 alt 是 "苹果 | 香蕉|w80"，还原后会变回 "苹果 | 香蕉"
      node.alt = realAltParts.join(' | ').trim();

      // 5. 注入 style 样式到 HTML 标签
      if (style) {
        node.data = node.data || {};
        node.data.hProperties = node.data.hProperties || {};
        node.data.hProperties.style = (node.data.hProperties.style || '') + style;
      }
    });
  };
};

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

// 解析 nav.json 为 Rspress 格式
function parseNavAndSidebar(config: any[]) {
  const nav: any[] = [];
  const sidebar: Record<string, any[]> = {};

  // 辅助函数：处理链接，将 xxx/index.md 或 xxx.md 转换为正确的路由
  const normalizeLink = (link: string) => {
    let normalized = link.replace(/\.md$/, '');
    if (normalized.endsWith('/index')) {
      normalized = normalized.slice(0, -6);
    }
    return `/${normalized}`;
  };

  config.forEach((item) => {
    // 处理导航栏
    const navItem: any = {
      text: item.title,
    };

    // 寻找导航项对应的链接 (通常是第一个子页面)
    const findFirstLink = (children: any[]): string | undefined => {
      for (const child of children) {
        if (typeof child === 'string') return normalizeLink(child);
        if (typeof child === 'object') {
          const keys = Object.keys(child);
          if (keys.length > 0 && Array.isArray(child[keys[0]])) {
            return findFirstLink(child[keys[0]]);
          }
        }
      }
      return undefined;
    };

    if (item.children) {
      const link = findFirstLink(item.children);
      if (link) {
        navItem.link = link;
      }

      // 处理侧边栏
      const sidebarItems = item.children.map((child: any) => {
        if (typeof child === 'string') {
          // 如果 nav.json 中直接写了路径，也需要处理（虽然 Rspress 侧边栏支持字符串路径，但我们统一样式）
          return {
            text: path.basename(child, '.md'),
            link: normalizeLink(child),
          };
        } else {
          // 处理嵌套结构，例如 {"分类名": ["path/to/doc.md"]}
          const sectionTitle = Object.keys(child)[0];
          return {
            text: sectionTitle,
            collapsible: true,
            collapsed: false,
            items: child[sectionTitle].map((sub: string) => {
              let text = path.basename(sub, '.md');
              if (text === 'index') {
                // 如果是 index.md，则取其父目录名作为标题（或者根据实际需求调整）
                const parts = sub.split('/');
                text = parts[parts.length - 2] || 'Index';
              }
              return {
                text: text,
                link: normalizeLink(sub),
              };
            }),
          };
        }
      });

      // 如果有子项，则将其分配给对应的侧边栏分组
      if (link) {
        const parts = link.split('/').filter(Boolean);
        const prefix = parts.length > 0 ? `/${parts[0]}/` : '/';
        sidebar[prefix] = sidebarItems;
      }
    }

    nav.push(navItem);
  });

  return { nav, sidebar };
}

const { nav, sidebar } = parseNavAndSidebar(navConfig);

// 支持的社交链接图标
const SUPPORTED_SOCIAL_ICONS = [
  'lark', 'discord', 'facebook', 'github', 'instagram', 'linkedin',
  'slack', 'x', 'youtube', 'wechat', 'qq', 'juejin', 'zhihu',
  'bilibili', 'weibo', 'gitlab', 'X', 'bluesky', 'npm'
];

export default defineConfig({
  root: path.join(__dirname, 'docs'),
  base: base,
  title: projectConfig.info.site_name,
  description: projectConfig.info.site_description,
  lang: 'zh',
  logoText: projectConfig.info.site_name,
  icon: `./docs/${projectConfig.theme.favicon}`,
  logo: `./${projectConfig.theme.logo}`,
  llms: true,
  globalStyles: path.join(__dirname, 'styles/custom.css'),
  markdown: {
    showLineNumbers: true,
    shiki: {
      defaultLanguage: 'text',
      fallbackLanguage: 'text'
    },
    remarkPlugins: [remarkCodeBlockToMath, remarkGfm, remarkCjkFriendly, remarkEmoji] as any,
    rehypePlugins: [] as any,
  },
  builderConfig: {
    html: {
      tags: [
        {
          tag: 'link',
          attrs: {
            rel: 'stylesheet',
            href: 'https://cdn.jsdelivr.net/npm/katex@0.16.27/dist/katex-swap.min.css',
          },
          append: false,
        }
      ]
    }
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
    socialLinks: (extraConfig.social || []).map((s: any) => {
      let icon = s.icon;

      // 如果已经是对象格式 { svg: '...' }
      if (typeof icon === 'object' && icon !== null && icon.svg) {
        return {
          icon: icon,
          mode: 'link',
          content: s.link,
        };
      }

      // 处理旧的 fontawesome 路径或 url 编码路径
      if (typeof icon === 'string' && icon.includes('/')) {
        const parts = icon.split('/');
        icon = parts[parts.length - 1].replace('x-twitter', 'x');
      }

      // 如果是自定义 SVG 字符串
      if (typeof icon === 'string' && icon.trim().startsWith('<svg')) {
        return {
          icon: { svg: icon },
          mode: 'link',
          content: s.link,
        };
      }

      // 仅保留支持的内置图标
      if (typeof icon === 'string' && SUPPORTED_SOCIAL_ICONS.includes(icon)) {
        return {
          icon: icon,
          mode: 'link',
          content: s.link,
        };
      }

      return null;
    }).filter(Boolean),
    editLink: {
      docRepoBaseUrl: `${projectConfig.info.repo_url}/blob/main/docs/`,
    },
  },
  plugins: [
    localKatexPlugin(),
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
