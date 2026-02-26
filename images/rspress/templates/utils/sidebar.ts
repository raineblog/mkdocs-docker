import path from 'path';
import fs from 'fs';

export const normalizeLink = (link: string) => {
  let normalized = link.replace(/\.md$/, '');
  if (normalized.endsWith('/index')) {
    normalized = normalized.slice(0, -6);
  }
  // Rspress 路由必须以 / 开头，且不应有双斜杠
  const result = normalized.startsWith('/') ? normalized : `/${normalized}`;
  return result === '' ? '/' : result;
};

/**
 * 从 Markdown 文件中读取第一个非空行作为标题
 */
const getTitleFromFile = (fullPath: string): string => {
  try {
    if (!fs.existsSync(fullPath)) return '无标题';
    const content = fs.readFileSync(fullPath, 'utf-8');
    const lines = content.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed) {
        // 如果是 H1，去除 # 和可能的标识符
        if (trimmed.startsWith('#')) {
          return trimmed.replace(/^#+\s*/, '').replace(/\{#.*\}\s*$/, '').trim();
        }
        return trimmed;
      }
    }
  } catch (e) {
    console.error(`Failed to read title from ${fullPath}:`, e);
  }
  return '无标题';
};

export function parseNavAndSidebar(config: any[], docsDir: string) {
  const nav: any[] = [];
  const sidebar: Record<string, any[]> = {};

  // 辅助函数：寻找第一个有效的页面路径作为目录的跳转链接
  const findFirstLink = (children: any[]): string | undefined => {
    for (const child of children) {
      if (typeof child === 'string') return normalizeLink(child);
      if (typeof child === 'object') {
        const keys = Object.keys(child);
        if (keys.length > 0 && Array.isArray(child[keys[0]])) {
          const l = findFirstLink(child[keys[0]]);
          if (l) return l;
        }
      }
    }
    return undefined;
  };

  config.forEach((item) => {
    const navItem: any = {
      text: item.title,
    };

    if (item.children) {
      const firstLink = findFirstLink(item.children);
      if (firstLink) {
        navItem.link = firstLink;
      }

      // 处理侧边栏：Rspress 2.0 推荐的结构
      const sidebarItems = item.children.map((child: any) => {
        if (typeof child === 'string') {
          const fullPath = path.join(docsDir, child);
          return {
            text: getTitleFromFile(fullPath),
            link: normalizeLink(child),
          };
        } else {
          // 处理嵌套映射 {"分类名": ["paths..."]}
          const sectionTitle = Object.keys(child)[0];
          return {
            text: sectionTitle,
            collapsible: true,
            collapsed: false,
            items: child[sectionTitle].map((sub: string) => {
              const fullPath = path.join(docsDir, sub);
              return {
                text: getTitleFromFile(fullPath),
                link: normalizeLink(sub),
              };
            }),
          };
        }
      });

      // 根据前缀分配侧边栏
      if (firstLink) {
        const parts = firstLink.split('/').filter(Boolean);
        const prefix = parts.length > 0 ? `/${parts[0]}/` : '/';
        sidebar[prefix] = sidebarItems;
      }
    }

    nav.push(navItem);
  });

  return { nav, sidebar };
}
