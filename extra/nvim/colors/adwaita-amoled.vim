" =============================================================================
" adwaita-amoled.vim — Neovim colorscheme
" GNOME Adwaita Dark adapted for AMOLED displays (pure #000000 background)
" =============================================================================

set background=dark
hi clear
if exists('syntax_on') | syntax reset | endif
let g:colors_name = 'adwaita-amoled'

" Requires set termguicolors in your init.vim / init.lua

" =============================================================================
" Palette
" =============================================================================
"
"   Surface
"   bg            #000000   pure AMOLED black   (NONE for terminal transparency)
"   surface_card  #0f0f0f
"   surface_hover #1a1a1a
"   border        #2a2a2a
"   ghost         #555555   ~3.5:1 on bg
"   disabled      #c0c0c0  11.54:1
"   fg            #ffffff  21.00:1
"
"   Accent (blue)
"   accent_active #2d6be0   4.29:1
"   accent        #387af2   5.23:1
"   accent_hover  #4a8cf5   6.36:1
"
"   Semantic
"   error         #ff0000   5.25:1     bright_error   #ff4444   6.16:1
"   success       #0aeea0  13.75:1     bright_success #4affc4  16.39:1
"   warning       #f1ac00  10.64:1     bright_warning #ffcc44  13.97:1
"   cyan          #01c1f1   9.90:1     bright_cyan    #44ddff  13.03:1
"   magenta       #c678dd   7.13:1     bright_magenta #e599ff  10.33:1
"
" =============================================================================

" -----------------------------------------------------------------------------
" Editor chrome
" -----------------------------------------------------------------------------
hi Normal          guifg=#ffffff   guibg=NONE      gui=NONE
hi NormalNC        guifg=#c0c0c0   guibg=NONE      gui=NONE
hi NormalFloat     guifg=#ffffff   guibg=#0f0f0f   gui=NONE

hi LineNr          guifg=#555555   guibg=NONE      gui=NONE
hi CursorLineNr    guifg=#f1ac00   guibg=NONE      gui=bold
hi CursorLine      guifg=NONE      guibg=#0f0f0f   gui=NONE
hi ColorColumn     guifg=NONE      guibg=#0f0f0f   gui=NONE
hi SignColumn      guifg=#555555   guibg=NONE      gui=NONE
hi FoldColumn      guifg=#555555   guibg=NONE      gui=NONE
hi Folded          guifg=#555555   guibg=#0f0f0f   gui=italic
hi EndOfBuffer     guifg=#2a2a2a   guibg=NONE      gui=NONE
hi NonText         guifg=#2a2a2a   guibg=NONE      gui=NONE
hi Whitespace      guifg=#2a2a2a   guibg=NONE      gui=NONE
hi SpecialKey      guifg=#2a2a2a   guibg=NONE      gui=NONE
hi Conceal         guifg=#555555   guibg=NONE      gui=NONE

hi WinSeparator    guifg=#2a2a2a   guibg=NONE      gui=NONE
hi VertSplit       guifg=#2a2a2a   guibg=NONE      gui=NONE

" -----------------------------------------------------------------------------
" Status / tab line
" -----------------------------------------------------------------------------
hi StatusLine      guifg=#c0c0c0   guibg=#0f0f0f   gui=NONE
hi StatusLineNC    guifg=#555555   guibg=#0f0f0f   gui=NONE
hi TabLine         guifg=#555555   guibg=#0f0f0f   gui=NONE
hi TabLineSel      guifg=#ffffff   guibg=NONE      gui=bold
hi TabLineFill     guifg=NONE      guibg=#0f0f0f   gui=NONE

" -----------------------------------------------------------------------------
" Selection / search
" -----------------------------------------------------------------------------
hi Visual          guifg=NONE      guibg=#1a1a1a   gui=NONE
hi VisualNOS       guifg=NONE      guibg=#1a1a1a   gui=NONE
hi Search          guifg=#387af2   guibg=#0f0f0f   gui=bold
hi IncSearch       guifg=#ffffff   guibg=#387af2   gui=bold
hi CurSearch       guifg=#ffffff   guibg=#387af2   gui=bold
hi MatchParen      guifg=#f1ac00   guibg=NONE      gui=bold,underline

" -----------------------------------------------------------------------------
" Popup / completion menu
" -----------------------------------------------------------------------------
hi Pmenu           guifg=#ffffff   guibg=#0f0f0f   gui=NONE
hi PmenuSel        guifg=#000000   guibg=#387af2   gui=bold
hi PmenuSbar       guifg=NONE      guibg=#1a1a1a   gui=NONE
hi PmenuThumb      guifg=NONE      guibg=#387af2   gui=NONE

" -----------------------------------------------------------------------------
" Messages & prompts
" -----------------------------------------------------------------------------
hi ErrorMsg        guifg=#ff0000   guibg=NONE      gui=bold
hi WarningMsg      guifg=#f1ac00   guibg=NONE      gui=NONE
hi ModeMsg         guifg=#0aeea0   guibg=NONE      gui=bold
hi MsgArea         guifg=#c0c0c0   guibg=NONE      gui=NONE
hi MsgSeparator    guifg=#2a2a2a   guibg=NONE      gui=NONE
hi MoreMsg         guifg=#0aeea0   guibg=NONE      gui=bold
hi Question        guifg=#0aeea0   guibg=NONE      gui=NONE

" -----------------------------------------------------------------------------
" Diff
" -----------------------------------------------------------------------------
hi DiffAdd         guifg=#0aeea0   guibg=#001a0f   gui=NONE
hi DiffChange      guifg=#f1ac00   guibg=#141000   gui=NONE
hi DiffDelete      guifg=#ff0000   guibg=#140000   gui=NONE
hi DiffText        guifg=#ffffff   guibg=#387af2   gui=bold

" -----------------------------------------------------------------------------
" Spell
" -----------------------------------------------------------------------------
hi SpellBad        guifg=NONE      guibg=NONE      gui=undercurl   guisp=#ff0000
hi SpellCap        guifg=NONE      guibg=NONE      gui=undercurl   guisp=#f1ac00
hi SpellRare       guifg=NONE      guibg=NONE      gui=undercurl   guisp=#c678dd
hi SpellLocal      guifg=NONE      guibg=NONE      gui=undercurl   guisp=#01c1f1

" -----------------------------------------------------------------------------
" Diagnostics (LSP / nvim-lsp)
" -----------------------------------------------------------------------------
hi DiagnosticError              guifg=#ff0000   guibg=NONE   gui=NONE
hi DiagnosticWarn               guifg=#f1ac00   guibg=NONE   gui=NONE
hi DiagnosticInfo               guifg=#387af2   guibg=NONE   gui=NONE
hi DiagnosticHint               guifg=#555555   guibg=NONE   gui=NONE
hi DiagnosticUnderlineError     guifg=NONE      guibg=NONE   gui=undercurl   guisp=#ff0000
hi DiagnosticUnderlineWarn      guifg=NONE      guibg=NONE   gui=undercurl   guisp=#f1ac00
hi DiagnosticUnderlineInfo      guifg=NONE      guibg=NONE   gui=undercurl   guisp=#387af2
hi DiagnosticUnderlineHint      guifg=NONE      guibg=NONE   gui=undercurl   guisp=#555555

" -----------------------------------------------------------------------------
" Syntax — base groups  (all other groups link to these)
" -----------------------------------------------------------------------------
hi Comment         guifg=#555555   guibg=NONE   gui=italic

hi Constant        guifg=#4affc4   guibg=NONE   gui=NONE
hi String          guifg=#f1ac00   guibg=NONE   gui=NONE
hi Character       guifg=#f1ac00   guibg=NONE   gui=NONE
hi Number          guifg=#4affc4   guibg=NONE   gui=NONE
hi Boolean         guifg=#ff4444   guibg=NONE   gui=bold
hi Float           guifg=#4affc4   guibg=NONE   gui=NONE

hi Identifier      guifg=#ffffff   guibg=NONE   gui=NONE
hi Function        guifg=#0aeea0   guibg=NONE   gui=bold

hi Statement       guifg=#387af2   guibg=NONE   gui=bold
hi Conditional     guifg=#387af2   guibg=NONE   gui=bold
hi Repeat          guifg=#387af2   guibg=NONE   gui=bold
hi Label           guifg=#4a8cf5   guibg=NONE   gui=NONE
hi Operator        guifg=#01c1f1   guibg=NONE   gui=NONE
hi Keyword         guifg=#387af2   guibg=NONE   gui=bold
hi Exception       guifg=#ff4444   guibg=NONE   gui=bold

hi PreProc         guifg=#c678dd   guibg=NONE   gui=NONE
hi Include         guifg=#c678dd   guibg=NONE   gui=NONE
hi Define          guifg=#c678dd   guibg=NONE   gui=NONE
hi Macro           guifg=#e599ff   guibg=NONE   gui=NONE
hi PreCondit       guifg=#c678dd   guibg=NONE   gui=NONE

hi Type            guifg=#4a8cf5   guibg=NONE   gui=bold
hi StorageClass    guifg=#4a8cf5   guibg=NONE   gui=NONE
hi Structure       guifg=#4a8cf5   guibg=NONE   gui=NONE
hi Typedef         guifg=#4a8cf5   guibg=NONE   gui=NONE

hi Special         guifg=#01c1f1   guibg=NONE   gui=NONE
hi SpecialChar     guifg=#44ddff   guibg=NONE   gui=NONE
hi Tag             guifg=#387af2   guibg=NONE   gui=NONE
hi Delimiter       guifg=#c0c0c0   guibg=NONE   gui=NONE
hi SpecialComment  guifg=#555555   guibg=NONE   gui=bold
hi Debug           guifg=#ff4444   guibg=NONE   gui=NONE

hi Underlined      guifg=NONE      guibg=NONE   gui=underline
hi Ignore          guifg=#2a2a2a   guibg=NONE   gui=NONE
hi Error           guifg=#ff0000   guibg=NONE   gui=bold
hi Todo            guifg=#000000   guibg=#f1ac00 gui=bold

" -----------------------------------------------------------------------------
" Misc UI
" -----------------------------------------------------------------------------
hi Title           guifg=#387af2   guibg=NONE   gui=bold
hi Directory       guifg=#387af2   guibg=NONE   gui=bold
hi WildMenu        guifg=#000000   guibg=#387af2 gui=bold
hi QuickFixLine    guifg=NONE      guibg=#1a1a1a gui=NONE

" -----------------------------------------------------------------------------
" vim-airline (base16 / custom theme hint)
" See :help airline-customization
" -----------------------------------------------------------------------------
" airline picks up Normal/StatusLine automatically; the palette below
" overrides its accent color to match @accent.
let g:airline_theme = 'adwaita_amoled'

" If the airline theme file is not present, the built-in 'dark' theme is a
" fine fallback: add  let g:airline_theme = 'dark'  to your init.vim.

" =============================================================================
" vim: ft=vim sw=4 ts=4
