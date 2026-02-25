-- html-cleanup-v2.lua
-- HTML → commonmark_x 终极清理版（支持任意嵌套 callout + 完整反转义 + 元数据提取）

local function unescape_math(s)
  if not s then return "" end
  if type(s) ~= "string" then
    s = pandoc.utils.stringify(s)
  end
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

-- 转换元数据（如果需要作为 frontmatter 写入）
function Pandoc(doc)
    local meta = doc.meta
    -- 尝试从 RawBlocks 中搜寻元数据（启发式）
    for i, el in ipairs(doc.blocks) do
        if el.t == "RawBlock" and el.format == "html" then
            local title = el.text:match('data%-title="([^"]+)"')
            local url = el.text:match('data%-url="([^"]+)"')
            if title then meta.title = title end
            if url then meta.url = url end
        end
    end
    
    -- 移除那些提取完后的元数据注释
    local new_blocks = pandoc.List()
    for _, el in ipairs(doc.blocks) do
        local skip = false
        if el.t == "RawBlock" and el.format == "html" then
            if el.text:match('mkdocs%-fragment') or el.text:match('</article>') then
                skip = true
            end
        end
        if not skip then
            new_blocks:insert(el)
        end
    end
    doc.blocks = new_blocks
    return doc
end

-- 2. Inline arithmatex: [\$F_1\'\$] → $F_1'$
function Span(el)
  if el.classes and el.classes:includes("arithmatex") then
    local text = pandoc.utils.stringify(el.content)
    text = unescape_math(text)
    -- 确保是单 $ 包裹
    return pandoc.RawInline("markdown", "$" .. text .. "$")
  end
end

-- 3. Block arithmatex + Admonition
function Div(el)
  -- arithmatex display math
  if el.classes and el.classes:includes("arithmatex") then
    local text = pandoc.utils.stringify(el.content)
    text = unescape_math(text)
    -- 修复 $$ 与内容之间的换行。
    -- 如果直接写 "\n\n" 会导致多余空行，这里使用 "\n" 
    return pandoc.RawBlock("markdown", "$$\n" .. text .. "\n$$")
  end

  -- 识别 callout 类型
  local callout_type = nil
  for _, t in ipairs(admon_types) do
    if el.classes and el.classes:includes(t) then
      callout_type = t
      break
    end
  end
  if not callout_type and el.classes and (el.classes:includes("admonition") or el.classes:includes("details")) then
    callout_type = "note"
  end

  if callout_type then
    -- 提取标题
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

    local inner_md = pandoc.write(pandoc.Pandoc(body), "commonmark_x")
    local fence_len = math.max(3, max_fence_length(inner_md) + 1)
    local fence = string.rep(":", fence_len)

    local opening = fence .. callout_type
    if title and title ~= "" then
      opening = opening .. " " .. title
    end

    local full_md = opening .. "\n\n" .. inner_md .. "\n" .. fence .. "\n"
    return pandoc.RawBlock("markdown", full_md)
  end

  -- 处理多余的容器（如 .grid 或 .v-pre 等非语义化 Div）
  -- 如果 Div 只有渲染意义而用户不希望在 Markdown 中保留 ::: {.grid}
  if el.classes and (el.classes:includes("grid") or el.classes:includes("v-pre")) then
    return el.content
  end

  return el
end

-- 4. 代码块清理 (CodeBlock)
function CodeBlock(el)
  -- 提取真正的语言类名 (language-xxx -> xxx)
  local lang = nil
  for _, class in ipairs(el.classes) do
    if class:match("^language%-") then
      lang = class:match("^language%-(.+)")
      break
    end
  end

  -- 如果只有 highlight 类，或者识别到了具体的语言
  if lang then
    el.classes = {lang}
  elseif el.classes:includes("highlight") then
    -- 启发式判断：如果内容包含 python 关键字或特定的 exptree
    if el.text:match("exptree%(") or el.text:match("import ") or el.text:match("def ") then
      el.classes = {"python"}
    elseif el.text:match("^git ") or el.text:match("^cd ") or el.text:match("^submodule ") then
      el.classes = {"sh"}
    else
      -- 默认清理掉 highlight，让它变成无语言代码块或保持原样
      -- 这里根据用户要求，如果识别不出，先尝试设为 text 或清理
      el.classes = {}
    end
  end

  return el
end

-- 5. 图片处理 (原样输出为 raw html tag)
local function img_to_html(el)
  local html = '<img src="' .. el.src .. '"'
  
  if el.classes and #el.classes > 0 then
    html = html .. ' class="' .. table.concat(el.classes, ' '):gsub('"', '&quot;') .. '"'
  end
  if el.identifier and el.identifier ~= "" then
    html = html .. ' id="' .. el.identifier:gsub('"', '&quot;') .. '"'
  end
  for k, v in pairs(el.attributes) do
    if k ~= "src" and k ~= "alt" and k ~= "title" then
      html = html .. ' ' .. k .. '="' .. v:gsub('"', '&quot;') .. '"'
    end
  end
  
  if el.title and el.title ~= "" then
    html = html .. ' title="' .. el.title:gsub('"', '&quot;') .. '"'
  end
  
  local alt = pandoc.utils.stringify(el.caption)
  if alt and alt ~= "" then
    html = html .. ' alt="' .. alt:gsub('"', '&quot;') .. '"'
  end
  
  html = html .. '>'
  return html
end

function Para(el)
  if #el.content == 1 and el.content[1].t == "Image" then
    return pandoc.RawBlock("markdown", img_to_html(el.content[1]))
  end
end

function Plain(el)
  if #el.content == 1 and el.content[1].t == "Image" then
    return pandoc.RawBlock("markdown", img_to_html(el.content[1]))
  end
end

function Image(el)
  return pandoc.RawInline("markdown", img_to_html(el))
end

return {
  {Pandoc = Pandoc},
  {Span = Span},
  {Div = Div},
  {CodeBlock = CodeBlock},
  {Para = Para, Plain = Plain},
  {Image = Image}
}
