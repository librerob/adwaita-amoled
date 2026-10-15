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
end)
if not ok then
  io.stderr:write(tostring(err) .. '\n')
  vim.cmd('cquit 1')
else
  vim.cmd('qa!')
end
