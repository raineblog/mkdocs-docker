export const SUPPORTED_SOCIAL_ICONS = [
  'lark', 'discord', 'facebook', 'github', 'instagram', 'linkedin',
  'slack', 'x', 'youtube', 'wechat', 'qq', 'juejin', 'zhihu',
  'bilibili', 'weibo', 'gitlab', 'X', 'bluesky', 'npm'
];

export const CUSTOM_SOCIAL_ICONS: Record<string, string> = {
  wechat: '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="20" height="20"><path d="M661.1 230.1c-161.3 0-292.1 117.4-292.1 262.2 0 78.4 38.6 148.9 99 198.5l-25.2 75.3 84.1-42.3c39.1 19.3 85.5 30.7 134.2 30.7 161.3 0 292.1-117.4 292.1-262.2s-130.8-262.2-292.1-262.2zm-126.9 167.3c-21.6 0-39.1-17.5-39.1-39s17.5-39.1 39.1-39.1 39.1 17.5 39.1 39.1c0 21.4-17.5 39-39.1 39zm253.9 0c-21.6 0-39.1-17.5-39.1-39s17.5-39.1 39.1-39.1c21.6 0 39.1 17.5 39.1 39.1.1 21.4-17.4 39-39.1 39zM425.8 456.9C425.8 288.5 275 152 89.2 152 29.6 152 0 288.5 0 456.9c0 98.7 51.1 186.2 129.8 247.9l-33.1 99.3 111.9-56.1c51.9 24.3 112 37.9 177.2 37.9 185.8 0 336.7-136.5 336.7-304.9.1-8-116.7-24.1-396.7-24.1zm-136.1-99.3c-27 0-48.9-21.9-48.9-48.9s21.9-48.9 48.9-48.9 48.9 21.9 48.9 48.9-21.9 48.9-48.9 48.9zm241.8 0c-27 0-48.9-21.9-48.9-48.9s21.9-48.9 48.9-48.9 48.9 21.9 48.9 48.9-21.9 48.9-48.9 48.9z" fill="currentColor"/></svg>',
  zhihu: '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="20" height="20"><path d="M547.4 396.9h181.7l13.9 31.6s-1.3 64.1-1.3 103.8H538.1l-60.6-31.6s2.5-126.3 3.8-191.0c27.1 2.9 59.8 9 59.8 9l6.3 78.2zm238.2 214.2l34.1 48.1s-111.4 125.8-232.0 207.3L540.8 808c46.1-32.3 244.8-196.9 244.8-196.9zm65.9-267.3V628h-68.4s-13.9 119.5-144.1 199.1c-13.9 9-45.6 16.4-45.6 16.4l-11.4-60.6c31.6-16.5 137.9-88.6 137.9-154.9h-89.1V343.8h220.7zM330.1 760.3L232.8 912l-77.1-41.7 54.4-88.5h-97.3V343.8h305.9v434.9h-88.6V760.3zM149.2 405.5h164.4v304.7L149.2 405.5zm164.4 75.9h-43s-40.5 63.3-64.5 102.4l107.5-102.4zM394.4 191.0v630.7H318.5V191.0h75.9z" fill="currentColor"/></svg>',
  juejin: '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="20" height="20"><path d="M512 87.058l363.364 282.607-363.364 282.61L148.636 369.665 512 87.058zm0 188.404L323.018 369.665 512 516.487l188.982-146.822L512 275.462zm0 376.812l363.364 282.607-363.364 282.61-363.364-282.61L512 652.274zm0 188.404l-188.982 94.202L512 1024l188.982-89.124L512 840.678z" fill="currentColor"/></svg>',
  bilibili: '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="20" height="20"><path d="M239.1 113.8a42.9 42.9 0 0 1 54.6-25c11.7 3.9 22.8 19.3 22.8 19.3L443 234.6h138l126.5-126.5s12.5-12.5 25-15.4c12.5-2.9 24.3 6.6 24.3 6.6 24.5 20.8 17.6 42.4 17.6 42.4L719.5 200.7l23.5 1s115 .6 182 66.8c67 66.2 87.6 179.6 87.6 179.6l10.3 355.8s-4 122.3-108.5 186c-104.5 63.7-212 63.7-212 63.7h-362s-133.5-.8-216.5-66c-83-65.2-112-182.5-112-182.5L1.3 438s3-149.2 92.8-223.5c89.8-74.3 145-100.7 145-100.7zM203 795.1h618V385.4H203v409.7zm116.3-294.5h83v124h-83v-124zm306.4 0h83v124h-83v-124z" fill="currentColor"/></svg>',
};

export function mapSocialLinks(social: any[]): any[] {
  return (social || []).map((s: any) => {
    let icon = s.icon;

    if (typeof icon === 'object' && icon !== null && icon.svg) {
      return {
        icon: icon,
        mode: 'link',
        content: s.link,
      };
    }

    if (typeof icon === 'string' && icon.includes('/')) {
      const parts = icon.split('/');
      icon = parts[parts.length - 1].replace('x-twitter', 'x');
    }

    if (typeof icon === 'string') {
        const trimmedIcon = icon.trim();
        if (trimmedIcon.startsWith('<svg')) {
            return {
                icon: { svg: icon },
                mode: 'link',
                content: s.link,
            };
        }
        if (CUSTOM_SOCIAL_ICONS[icon]) {
            return {
                icon: { svg: CUSTOM_SOCIAL_ICONS[icon] },
                mode: 'link',
                content: s.link,
            };
        }
    }

    if (typeof icon === 'string' && SUPPORTED_SOCIAL_ICONS.includes(icon)) {
      return {
        icon: icon,
        mode: 'link',
        content: s.link,
      };
    }

    // fallback to github if unknown
    return {
      icon: 'github',
      mode: 'link',
      content: s.link,
    };
  });
}
