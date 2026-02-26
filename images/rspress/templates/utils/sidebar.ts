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
 * 从 Markdown 文件中读取标题
 * 规则：跳过 YAML Frontmatter，获取第一个非空行。如果是 H1 则提取文字，否则返回“无标题”。
 */
const getTitleFromFile = (fullPath: string): string => {
  try {
    if (!fs.existsSync(fullPath)) {
      // 调试日志：如果找不到文件，打印路径
      console.warn(`[Sidebar] File not found: ${fullPath}`);
      return '无标题';
    }
    const content = fs.readFileSync(fullPath, 'utf-8');
    const lines = content.split(/\r?\n/);
    
    let inFrontmatter = false;
    let lineIdx = 0;

    // 检查是否有 Frontmatter 
    if (lines[0] && lines[0].trim() === '---') {
      inFrontmatter = true;
      lineIdx = 1;
      while (lineIdx < lines.length) {
        if (lines[lineIdx].trim() === '---') {
          inFrontmatter = false;
          lineIdx++;
          break;
        }
        lineIdx++;
      }
    }

    // 寻找第一个非空行
    for (let i = lineIdx; i < lines.length; i++) {
        const trimmed = lines[i].trim();
        if (trimmed) {
            // 如果是 H1
            if (trimmed.startsWith('# ')) {
                // 移除 # 和可能的 identifier {#id}
                const title = trimmed.replace(/^#\s+/, '').replace(/\{#.*\}\s*$/, '').trim();
                return title || '无标题';
            } else if (trimmed.startsWith('#')) {
                // 处理没有空格的情况，如 #Title
                const title = trimmed.replace(/^#+\s*/, '').replace(/\{#.*\}\s*$/, '').trim();
                return title || '无标题';
            }
            // 第一个非空行不是 H1，根据需求返回“无标题”
            return '无标题';
        }
    }
  } catch (e) {
    console.error(`[Sidebar] Error reading title from ${fullPath}:`, e);
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
          const fullPath = path.resolve(docsDir, child);
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
              const fullPath = path.resolve(docsDir, sub);
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
