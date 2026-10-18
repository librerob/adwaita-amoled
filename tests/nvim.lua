local ok, err = pcall(function()
  vim.opt.runtimepath:append(vim.env.THEME_ROOT .. '/extra/nvim')
  vim.opt.termguicolors = true
  for _ = 1, 100 do vim.cmd('colorscheme adwaita-amoled') end
  assert(vim.g.colors_name == 'adwaita-amoled')
  for _, line in ipairs(vim.fn.readfile(vim.env.THEME_ROOT .. '/extra/nvim/colors/adwaita-amoled.vim')) do
    local group = line:match('^hi%s+([^%s]+)')
    if group and group ~= 'clear' then
      for key, attr in pairs({guifg = 'fg', guibg = 'bg', guisp = 'sp'}) do
        local value = line:match(key .. '=(#[%x]+)')
        if value then
          assert(vim.fn.synIDattr(vim.fn.hlID(group), attr, 'gui'):lower() == value:lower(), group .. ' ' .. attr)
        end
      end
    end
  end
  local structural = {
    WinSeparator=true, VertSplit=true, MsgSeparator=true,
    NvimTreeIndentMarker=true, NvimTreeWinSeparator=true,
    IblScope=true, IblIndent=true, IblWhitespace=true,
  }
  local backgrounds = {}
  for _, group in ipairs({'Normal', 'ColorColumn', 'NormalFloat', 'CursorLine', 'Visual'}) do
    local background = vim.fn.synIDattr(vim.fn.hlID(group), 'bg', 'gui')
    assert(background:match('^#%x%x%x%x%x%x$'), 'Missing background: ' .. group)
    table.insert(backgrounds, background)
  end
  local function lum(color)
    local result = 0
    for i, weight in ipairs({0.2126, 0.7152, 0.0722}) do
      local channel = tonumber(color:sub(i * 2, i * 2 + 1), 16) / 255
      result = result + (channel <= 0.04045 and channel / 12.92 or ((channel + 0.055) / 1.055) ^ 2.4) * weight
    end
    return result
  end
  local text_pairs = 0
  for _, line in ipairs(vim.fn.readfile(vim.env.THEME_ROOT .. '/extra/nvim/colors/adwaita-amoled.vim')) do
    local group = line:match('^hi%s+([^%s]+)')
    if group and group ~= 'EndOfBuffer' then
      local id = vim.fn.hlID(group)
      local fg = vim.fn.synIDattr(id, 'fg', 'gui')
      if fg:match('^#%x%x%x%x%x%x$') then
        local bg = vim.fn.synIDattr(id, 'bg', 'gui')
        local surfaces = bg:match('^#%x%x%x%x%x%x$') and {bg} or backgrounds
        for _, background in ipairs(surfaces) do
          local ratio = (math.max(lum(fg), lum(background)) + 0.05) / (math.min(lum(fg), lum(background)) + 0.05)
          assert(ratio >= (structural[group] and 3 or 4.5), group .. ' on ' .. background .. ' contrast ' .. ratio)
          text_pairs = text_pairs + 1
        end
      end
    end
  end
  assert(text_pairs > 500, 'Incomplete native Neovim color-role coverage')
  print('Neovim readability pairs: ' .. text_pairs)
  local airline_path = vim.env.THEME_AIRLINE_RUNTIME or '/usr/share/vim-airline'
  assert(vim.fn.isdirectory(airline_path) == 1, 'Install vim-airline for native palette checks')
  vim.opt.runtimepath:append(airline_path)
  vim.cmd('runtime autoload/airline/themes/adwaita_amoled.vim')
  local function xterm(index)
    if index < 16 then
      return ({'#000000','#800000','#008000','#808000','#000080','#800080','#008080','#c0c0c0',
               '#808080','#ff0000','#00ff00','#ffff00','#0000ff','#ff00ff','#00ffff','#ffffff'})[index + 1]
    elseif index < 232 then
      local value=index-16
      local levels={0,95,135,175,215,255}
      return string.format('#%02x%02x%02x',levels[math.floor(value/36)+1],levels[math.floor(value/6)%6+1],levels[value%6+1])
    end
    local value=8+(index-232)*10
    return string.format('#%02x%02x%02x',value,value,value)
  end
  local airline_pairs=0
  for mode, sections in pairs(vim.g['airline#themes#adwaita_amoled#palette']) do
    if mode ~= 'accents' then
      for section, colors in pairs(sections) do
        if type(colors)=='table' and #colors>=4 and colors[1]:match('^#') and colors[2]:match('^#') then
          for _, pair in ipairs({{colors[1],colors[2]},{xterm(colors[3]),xterm(colors[4])}}) do
            local ratio=(math.max(lum(pair[1]),lum(pair[2]))+.05)/(math.min(lum(pair[1]),lum(pair[2]))+.05)
            assert(ratio>=4.5,mode..'/'..section..' contrast '..ratio)
            airline_pairs=airline_pairs+1
          end
        end
      end
    end
  end
  assert(airline_pairs>=50,'Incomplete airline color coverage')
  print('Airline true-color/256-color pairs: '..airline_pairs)

  local selected = vim.fn.hlID('PmenuMatchSel')
  assert(vim.fn.synIDattr(selected, 'fg', 'gui') == '#000000')
  assert(vim.fn.synIDattr(selected, 'underline', 'gui') == '1')
  local function luminance(color)
    local value = 0
    for i, weight in ipairs({0.2126, 0.7152, 0.0722}) do
      local channel = tonumber(color:sub(i * 2, i * 2 + 1), 16) / 255
      local linear = channel <= 0.04045 and channel / 12.92 or ((channel + 0.055) / 1.055) ^ 2.4
      value = value + weight * linear
    end
    return value
  end
  for _, name in ipairs({'Folded', 'StatusLineNC', 'TabLine'}) do
    local id = vim.fn.hlID(name)
    local foreground = luminance(vim.fn.synIDattr(id, 'fg', 'gui'))
    local background = luminance(vim.fn.synIDattr(id, 'bg', 'gui'))
    local ratio = (math.max(foreground, background) + 0.05) / (math.min(foreground, background) + 0.05)
    assert(ratio >= 4.5, name .. ' contrast is ' .. ratio .. ':1')
  end
end)
if not ok then
  io.stderr:write(tostring(err) .. '\n')
  vim.cmd('cquit 1')
else
  vim.cmd('qa!')
end
