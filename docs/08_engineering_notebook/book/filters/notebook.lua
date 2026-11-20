-- Filtro de pandoc para el Libro de Ingeniería.
-- Variables de entorno: NB_SRC_DIR (carpeta del .md procesado), NB_REPO_ROOT.

local src_dir = os.getenv("NB_SRC_DIR") or "."
local image_ext = { png = true, jpg = true, jpeg = true, pdf = true }

local function file_exists(p)
  local f = io.open(p, "r")
  if f then f:close() return true end
  return false
end

local function normalize(path)
  local parts = {}
  for seg in path:gmatch("[^/]+") do
    if seg == ".." then table.remove(parts)
    elseif seg ~= "." then table.insert(parts, seg) end
  end
  return (path:sub(1, 1) == "/" and "/" or "") .. table.concat(parts, "/")
end

local function latex_escape(s)
  s = s:gsub("\\", "\\textbackslash{}")
  s = s:gsub("([&%%$#_{}])", "\\%1")
  s = s:gsub("~", "\\textasciitilde{}")
  s = s:gsub("%^", "\\textasciicircum{}")
  return s
end

-- Código en línea con puntos de corte para rutas y nombres largos.
function Code(el)
  local out = latex_escape(el.text)
  out = out:gsub("([/%.%-,=:])", "%1\\allowbreak{}")
  out = out:gsub("(\\_)", "%1\\allowbreak{}")
  return pandoc.RawInline("latex", "\\texttt{" .. out .. "}")
end

-- Enlaces relativos (a otros .md o carpetas) no existen en el PDF: se deja solo el texto.
function Link(el)
  local t = el.target
  if t:match("^https?://") or t:match("^mailto:") then
    return el
  end
  return el.content
end

function Image(el)
  local src = el.src
  if src:match("^https?://") then
    return pandoc.Str("[imagen externa omitida]")
  end
  local ext = (src:match("%.([%w]+)$") or ""):lower()
  local full = normalize(src:sub(1, 1) == "/" and src or (src_dir .. "/" .. src))
  if image_ext[ext] and file_exists(full) then
    el.src = full
    el.attributes["width"] = nil
    el.attributes["height"] = nil
    return el
  end
  return pandoc.Emph({ pandoc.Str("[figura no incluida: " .. src .. "]") })
end

-- Anchos de columna proporcionales al contenido (las tablas pipe de markdown no los traen).
function Table(tbl)
  local ncol = #tbl.colspecs
  if ncol == 0 then return nil end
  local total, longest = {}, {}
  local rows = 0
  for i = 1, ncol do total[i] = 0; longest[i] = 0 end
  local function add_row(row)
    rows = rows + 1
    for i, cell in ipairs(row.cells) do
      if i <= ncol then
        local text = pandoc.utils.stringify(cell.contents)
        total[i] = total[i] + math.min(#text, 400)
        for word in text:gmatch("%S+") do
          longest[i] = math.max(longest[i], math.min(#word, 22))
        end
      end
    end
  end
  for _, r in ipairs(tbl.head.rows) do add_row(r) end
  for _, b in ipairs(tbl.bodies) do
    for _, r in ipairs(b.body) do add_row(r) end
  end
  if rows == 0 then return nil end
  local weights, sum = {}, 0
  for i = 1, ncol do
    local avg = total[i] / rows
    weights[i] = math.max(math.min(avg, 70) ^ 0.85, longest[i] * 1.15, 6)
    sum = sum + weights[i]
  end
  for i = 1, ncol do
    tbl.colspecs[i] = { tbl.colspecs[i][1], weights[i] / sum }
  end
  if ncol >= 7 then
    return { pandoc.RawBlock("latex", "\\begingroup\\scriptsize"), tbl, pandoc.RawBlock("latex", "\\endgroup") }
  end
  return tbl
end

-- Los bloques HTML no se pueden representar en LaTeX.
function RawBlock(el)
  if el.format:match("html") then return {} end
end
function RawInline(el)
  if el.format:match("html") then return {} end
end
