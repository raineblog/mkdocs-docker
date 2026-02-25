import path from 'path';
import fs from 'fs';

import { defineConfig } from '@rspress/core';
import { pluginRss } from '@rspress/plugin-rss';
import { pluginSitemap } from '@rspress/plugin-sitemap';

import remarkGfm from 'remark-gfm';
import remarkCjkFriendly from "remark-cjk-friendly";

import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

import 'katex/dist/contrib/mhchem.min.js';
// import 'katex/dist/contrib/copy-tex.min.js';
// import 'katex/dist/contrib/mathtex-script-type.mjs';

import 'katex/dist/katex.min.css';


// @ts-ignore
import remarkImageAttributes from 'remark-image-attributes'

import remarkEmoji from 'remark-emoji';
import readingTime from 'rspress-plugin-reading-time';

import type { Plugin } from 'unified';
import { visit } from 'unist-util-visit';

const remarkCodeBlockToMath: Plugin = () => {
  return (tree) => {
    visit(tree, 'code', (node: any) => {
      // 匹配 ```math 语法的代码块
      if (node.lang === 'math') {
        
        // 1. 改变节点类型，伪装成原生的块级公式节点
        // 这将完美避开 Rspress/MDX 把代码块强制转为 <pre><code> 的行为
        node.type = 'math';
        
        // 2. 注入 rehype-katex 严格需要的数据结构
        node.data = {
          hName: 'div',
          hProperties: { className: ['math', 'math-display'] },
          // 【极其关键】必须把 node.value (公式文本) 塞进文本子节点里
          hChildren: [{ type: 'text', value: node.value }],
        };
        
        // 3. 打扫战场，删掉针对 code 节点的多余属性
        delete node.lang;
        delete node.meta;
      }
    });
  };
};

function localKatexPlugin() {
  const katexCss = require.resolve('katex/dist/katex.min.css');
  return {
    name: 'local-katex-plugin',
    globalStyles: katexCss,
    markdown: {
      remarkPlugins: [
        remarkMath,
        remarkCodeBlockToMath
      ] as any,
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
      remarkGfm,
      remarkCjkFriendly,
      remarkEmoji
    ] as any,
    rehypePlugins: [] as any,
  },
  // builderConfig: {
  //   html: {
  //     tags: [
  //       {
  //         tag: 'link',
  //         attrs: {
  //           rel: 'stylesheet',
  //           href: 'https://cdn.jsdelivr.net/npm/katex@0.16.27/dist/katex-swap.min.css',
  //         },
  //         append: false,
  //       }
  //     ]
  //   }
  // },
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
