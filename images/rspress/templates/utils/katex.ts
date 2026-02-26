import type { Plugin } from 'unified';
import { visit } from 'unist-util-visit';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/contrib/mhchem';

/**
 * 该插件将 ```math 代码块转换为 remark-math 的 math 节点，
 * 并确保所有 math 节点 (包括 $$ 产生的) 都能被 Rspress/MDX 正确识别。
 */
const remarkCodeBlockToMath: Plugin = () => {
  return (tree) => {
    visit(tree, ['code', 'math'], (node: any) => {
      // 1. 将 ```math 转换成 math 节点
      if (node.type === 'code' && node.lang === 'math') {
        node.type = 'math';
      }

      // 2. 对于所有的 math 节点 (包括原生 $$ 产生的)，注入 Rspress/MDX 需要的 HAST 信息
      // 这能确保即使后续 rehype-katex 没能及时处理，它也不会回退到 shiki 代码块
      if (node.type === 'math') {
        node.data = node.data || {};
        node.data.hName = 'div';
        node.data.hProperties = node.data.hProperties || {};
        node.data.hProperties.className = [
          ...(node.data.hProperties.className || []),
          'math',
          'math-display'
        ];
        // MDX 需要把内容推到 children 或特定的 data 属性中
        node.data.hChildren = [{ type: 'text', value: node.value }];
      }
    });
  };
};

export const remarkKatexPlugins = [
    remarkMath,
    remarkCodeBlockToMath
];

export const rehypeKatexPlugins = [
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
];
