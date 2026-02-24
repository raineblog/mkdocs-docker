-- html-cleanup-v2.lua
-- HTML → commonmark_x 终极清理版（支持任意嵌套 callout + 完整反转义）

local function unescape_math(s)
  if not s then return "" end
  s = pandoc.utils.stringify(s)
  -- HTML entities 完整解码
  s = s:gsub("&amp;", "&")
       :gsub("&lt;", "<")
       :gsub("&gt;", ">")
       :gsub("&quot;", '"')
       :gsub("&#39;", "'")
       :gsub("&#(%d+);", function(n) return utf8.char(tonumber(n)) end)
       :gsub("&#x([0-9a-fA-F]+);", function(h) return utf8.char(tonumber(h, 16)) end)
  -- LaTeX 转义反转（最常见情况）
  s = s:gsub("\\([%$%^_&%%#{}~\\])", "%1")
       :gsub("\\\\", "\\")
  return s:match("^%s*(.-)%s*$")
end

local admon_types = pandoc.List{
  "note", "tip", "info", "warning", "danger", "caution", "important",
  "abstract", "summary", "todo", "question", "hint", "example", "quote",
  "details", "success", "failure", "help"
}

-- 计算一段 markdown 里最长的开头冒号 fence（用于动态外层）
local function max_fence_length(str)
  local maxn = 2
  for line in str:gmatch("[^\r\n]+") do
    local cols = line:match("^:+")
    if cols and #cols > maxn then
      maxn = #cols
    end
  end
  return maxn
end

-- 1. Inline arithmatex: [\$F_1\'\$] → $F_1'$
function Span(el)
  if el.classes and el.classes:includes("arithmatex") then
    local text = pandoc.utils.stringify(el.content)
    text = text:gsub("^%s*%[", ""):gsub("%]%s*$", "")   -- 去 []
    text = unescape_math(text)
    return pandoc.Math("InlineMath", text)
  end
end

-- 2. Block arithmatex + Admonition + details
function Div(el)
  -- arithmatex display math
  if el.classes and el.classes:includes("arithmatex") then
    local text = pandoc.utils.stringify(el.content)
    text = text:gsub("^%s*[$]+", ""):gsub("[$]+%s*$", "")
    text = unescape_math(text)
    return pandoc.Math("DisplayMath", text)
  end

  -- 识别 callout 类型
  local callout_type = nil
  for _, t in ipairs(admon_types) do
    if el.classes and el.classes:includes(t) then
      callout_type = t
      break
    end
  end
  if not callout_type and el.classes and el.classes:includes("admonition") then
    callout_type = "note"
  end

  if callout_type then
    -- 提取标题（admonition-title / Header / <summary>）
    local title = nil
    local body = pandoc.List{}
    for _, blk in ipairs(el.content) do
      local is_title = false
      if blk.t == "Div" and blk.classes and blk.classes:includes("admonition-title") then
        title = pandoc.utils.stringify(blk.content):match("^%s*(.-)%s*$")
        is_title = true
      elseif blk.t == "Header" and blk.level <= 4 then
        title = pandoc.utils.stringify(blk.content):match("^%s*(.-)%s*$")
        is_title = true
      elseif (blk.t == "Para" or blk.t == "Plain") then
        local txt = pandoc.utils.stringify(blk)
        if txt:match("<summary>") then
          title = txt:match("<summary>(.-)</summary>") or txt
          is_title = true
        end
      end
      if not is_title then
        body:insert(blk)
      end
    end

    -- 写入内部内容（已经过 filter 处理）
    local inner_md = pandoc.write(pandoc.Pandoc(body), "commonmark_x")

    -- 动态 fence 长度：比内部最大多 1，保证嵌套绝对安全
    local fence_len = math.max(3, max_fence_length(inner_md) + 1)
    local fence = string.rep(":", fence_len)

    local opening = fence .. callout_type
    if title and title ~= "" then
      opening = opening .. " " .. title
    end

    local full_md = opening .. "\n\n" .. inner_md .. "\n" .. fence .. "\n"
    return pandoc.RawBlock("markdown", full_md)
  end

  return el
end

-- 3. 清除所有标题的 {#_1} {#_2} 等 id
function Header(el)
  el.identifier = ""
  return el
end

-- 4. 处理被 skipped 的 <details>
function RawBlock(el)
  if el.format == "html" and el.text:match("^%s*<details") then
    return pandoc.Div(pandoc.List{}, pandoc.Attr("", {"details"}))
  end
end

return {
  {Span = Span},
  {Div = Div},
  {Header = Header},
  {RawBlock = RawBlock}
}