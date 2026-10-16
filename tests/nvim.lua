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
