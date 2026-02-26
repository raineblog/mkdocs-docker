import path from 'path';

export const normalizeLink = (link: string) => {
  let normalized = link.replace(/\.md$/, '');
  if (normalized.endsWith('/index')) {
    normalized = normalized.slice(0, -6);
  }
  // Rspress 路由必须以 / 开头，且不应有双斜杠
  const result = normalized.startsWith('/') ? normalized : `/${normalized}`;
  return result === '' ? '/' : result;
};

export function parseNavAndSidebar(config: any[]) {
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
          return {
            text: path.basename(child, '.md').replace(/^\d+\./, '').trim(), // 移除数字前缀
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
              let text = path.basename(sub, '.md').replace(/^\d+\./, '').trim();
              if (text.toLowerCase() === 'index') {
                const parts = sub.split('/');
                text = parts[parts.length - 2] || 'Home';
              }
              return {
                text: text,
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
