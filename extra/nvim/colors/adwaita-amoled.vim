" =============================================================================
" adwaita-amoled.vim — Neovim colorscheme  (revised v2)
" GNOME Adwaita Dark adapted for AMOLED displays (pure #000000 background)
" =============================================================================
" Requires: set termguicolors in init.vim / init.lua
"           Neovim 0.9+ recommended (Treesitter + LSP semantic tokens)
" =============================================================================

set background=dark
hi clear
if exists('syntax_on') | syntax reset | endif
let g:colors_name = 'adwaita-amoled'

" =============================================================================
" Palette — with v2 contrast-corrected values annotated
" =============================================================================
"
"   Surface
"   bg            #000000   pure AMOLED black
"   surface_card  #0f0f0f                          (floats use #111820 — see below)
"   surface_hover #1a1a1a
"   border        #333333   1.66:1 vs bg            [FIX v2: was #2a2a2a 1.58:1]
"   ghost         #767676   4.62:1 vs bg            [FIX v2: was #555555 2.82:1]
"   ghost_ui      #737373   4.04:1 vs surface_card  [FIX v2: new; airline/statusline inactive]
"   disabled      #c0c0c0  11.54:1
"   fg            #ffffff  21.00:1
"
"   Accent (blue)
"   accent_active #2d6be0   4.29:1
"   accent        #387af2   5.23:1
"   accent_hover  #4a8cf5   6.36:1
"
"   Semantic
"   error         #ff3333   5.77:1  [FIX v2: was #ff0000 5.25:1 — harsh on OLED]
"   bright_error  #ff4444   6.16:1
"   success       #0aeea0  13.75:1    bright_success #4affc4  16.39:1
"   warning       #f1ac00  10.64:1    bright_warning #ffcc44  13.97:1
"   cyan          #01c1f1   9.90:1    bright_cyan    #44ddff  13.03:1
"   magenta       #c678dd   7.13:1    bright_magenta #e599ff  10.33:1
"   doc_comment   #8a8a8a   6.08:1  [FIX v2: new; doc comments brighter than code comments]
"
"   Selection / focus
"   visual_bg     #1a2d4a   blue-tinted; chromatic contrast on OLED  [FIX v2]
"   cursorline_bg #0c1a2e   darker blue tint — distinct from visual  [FIX v2]
"   float_bg      #111820   slightly elevated, blue-tinted surface    [FIX v2]
"
" =============================================================================

" ─────────────────────────────────────────────────────────────────────────────
" Editor chrome
" ─────────────────────────────────────────────────────────────────────────────
hi Normal          guifg=#ffffff   guibg=NONE      gui=NONE
hi NormalNC        guifg=#c0c0c0   guibg=NONE      gui=NONE

" Float bg is blue-tinted dark (#111820) — distinguishable from both bg
" (#000000) and surface_card (#0f0f0f) without breaking the AMOLED aesthetic.  [FIX v2]
hi NormalFloat     guifg=#ffffff   guibg=#111820   gui=NONE
hi FloatBorder     guifg=#387af2   guibg=#111820   gui=NONE
hi FloatTitle      guifg=#387af2   guibg=#111820   gui=bold

" Line numbers — #767676 (4.62:1); previously #555555 was 2.82:1.  [FIX v2]
hi LineNr          guifg=#767676   guibg=NONE      gui=NONE
hi CursorLineNr    guifg=#f1ac00   guibg=NONE      gui=bold
" CursorLine uses a dark blue tint — chromatically distinct from
" Visual (#1a2d4a) so cursor position and selection never blend.  [FIX v2]
hi CursorLine      guifg=NONE      guibg=#0c1a2e   gui=NONE
hi ColorColumn     guifg=NONE      guibg=#0f0f0f   gui=NONE

" SignColumn / FoldColumn — brought to #767676 for readability.  [FIX v2]
hi SignColumn      guifg=#767676   guibg=NONE      gui=NONE
hi FoldColumn      guifg=#767676   guibg=NONE      gui=NONE
hi Folded          guifg=#767676   guibg=#0f0f0f   gui=italic

hi EndOfBuffer     guifg=#333333   guibg=NONE      gui=NONE
hi NonText         guifg=#333333   guibg=NONE      gui=NONE
hi Whitespace      guifg=#333333   guibg=NONE      gui=NONE
hi SpecialKey      guifg=#333333   guibg=NONE      gui=NONE
hi Conceal         guifg=#767676   guibg=NONE      gui=NONE

" Window separators — #333333 (1.66:1 vs bg); subtle but visible.  [FIX v2: was #2a2a2a]
hi WinSeparator    guifg=#333333   guibg=NONE      gui=NONE
hi VertSplit       guifg=#333333   guibg=NONE      gui=NONE

" Window bar (breadcrumbs — Neovim 0.8+)
hi WinBar          guifg=#c0c0c0   guibg=NONE      gui=bold
hi WinBarNC        guifg=#767676   guibg=NONE      gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Status / tab line
" ─────────────────────────────────────────────────────────────────────────────
hi StatusLine      guifg=#c0c0c0   guibg=#0f0f0f   gui=NONE
" StatusLineNC bumped to #737373 (4.04:1 on surface) — was #555555 2.57:1.  [FIX v2]
hi StatusLineNC    guifg=#737373   guibg=#0f0f0f   gui=NONE
" TabLine inactive text bumped to #737373.  [FIX v2]
hi TabLine         guifg=#737373   guibg=#0f0f0f   gui=NONE
hi TabLineSel      guifg=#ffffff   guibg=NONE      gui=bold
hi TabLineFill     guifg=NONE      guibg=#0f0f0f   gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Selection / search
" ─────────────────────────────────────────────────────────────────────────────
" Visual uses a blue-tinted bg — chromatic contrast on OLED is strong even
" at modest luminance ratios. White text gives 13.83:1.  [FIX v2: was #1a1a1a 1.21:1]
hi Visual          guifg=NONE      guibg=#1a2d4a   gui=NONE
hi VisualNOS       guifg=NONE      guibg=#1a2d4a   gui=NONE

" Search (all matches): black text on warning yellow (#f1ac00) — 10.64:1.
" Much more scannable than the previous muted blue-text approach.  [FIX v2]
hi Search          guifg=#000000   guibg=#f1ac00   gui=bold
" Active/current match: white on accent blue (#387af2).
hi IncSearch       guifg=#ffffff   guibg=#387af2   gui=bold
hi CurSearch       guifg=#ffffff   guibg=#387af2   gui=bold

hi MatchParen      guifg=#f1ac00   guibg=NONE      gui=bold,underline

" ─────────────────────────────────────────────────────────────────────────────
" Substitution preview (:s///)
" ─────────────────────────────────────────────────────────────────────────────
hi Substitute      guifg=#000000   guibg=#f1ac00   gui=bold

" ─────────────────────────────────────────────────────────────────────────────
" Popup / completion menu
" ─────────────────────────────────────────────────────────────────────────────
hi Pmenu           guifg=#ffffff   guibg=#111820   gui=NONE
hi PmenuSel        guifg=#000000   guibg=#387af2   gui=bold
hi PmenuSbar       guifg=NONE      guibg=#1a1a1a   gui=NONE
hi PmenuThumb      guifg=NONE      guibg=#387af2   gui=NONE
hi PmenuMatch      guifg=#f1ac00   guibg=#111820   gui=bold
hi PmenuMatchSel   guifg=#f1ac00   guibg=#387af2   gui=bold

" ─────────────────────────────────────────────────────────────────────────────
" Messages & prompts
" ─────────────────────────────────────────────────────────────────────────────
" ErrorMsg uses softened error red.  [FIX v2]
hi ErrorMsg        guifg=#ff3333   guibg=NONE      gui=bold
hi WarningMsg      guifg=#f1ac00   guibg=NONE      gui=NONE
hi ModeMsg         guifg=#0aeea0   guibg=NONE      gui=bold
hi MsgArea         guifg=#c0c0c0   guibg=NONE      gui=NONE
hi MsgSeparator    guifg=#333333   guibg=NONE      gui=NONE
hi MoreMsg         guifg=#0aeea0   guibg=NONE      gui=bold
hi Question        guifg=#0aeea0   guibg=NONE      gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Diff
" ─────────────────────────────────────────────────────────────────────────────
hi DiffAdd         guifg=#0aeea0   guibg=#001a0f   gui=NONE   " 11.91:1
hi DiffChange      guifg=#f1ac00   guibg=#141000   gui=NONE   "  9.64:1
hi DiffDelete      guifg=#ff3333   guibg=#1a0000   gui=NONE   "  5.90:1  [FIX v2]
hi DiffText        guifg=#ffffff   guibg=#387af2   gui=bold

" ─────────────────────────────────────────────────────────────────────────────
" Spell
" ─────────────────────────────────────────────────────────────────────────────
hi SpellBad        guifg=NONE      guibg=NONE      gui=undercurl   guisp=#ff3333
hi SpellCap        guifg=NONE      guibg=NONE      gui=undercurl   guisp=#f1ac00
hi SpellRare       guifg=NONE      guibg=NONE      gui=undercurl   guisp=#c678dd
hi SpellLocal      guifg=NONE      guibg=NONE      gui=undercurl   guisp=#01c1f1

" ─────────────────────────────────────────────────────────────────────────────
" Diagnostics (LSP / nvim-lsp)
" ─────────────────────────────────────────────────────────────────────────────
" Error uses softened #ff3333.  [FIX v2]
hi DiagnosticError              guifg=#ff3333   guibg=NONE   gui=NONE
hi DiagnosticWarn               guifg=#f1ac00   guibg=NONE   gui=NONE
hi DiagnosticInfo               guifg=#387af2   guibg=NONE   gui=NONE
" DiagnosticHint bumped to #767676 (4.62:1) — was #555555 2.82:1.  [FIX v2]
hi DiagnosticHint               guifg=#767676   guibg=NONE   gui=NONE
hi DiagnosticOk                 guifg=#0aeea0   guibg=NONE   gui=NONE

hi DiagnosticUnderlineError     guifg=NONE      guibg=NONE   gui=undercurl   guisp=#ff3333
hi DiagnosticUnderlineWarn      guifg=NONE      guibg=NONE   gui=undercurl   guisp=#f1ac00
hi DiagnosticUnderlineInfo      guifg=NONE      guibg=NONE   gui=undercurl   guisp=#387af2
" Hint squiggle bumped to #767676.  [FIX v2]
hi DiagnosticUnderlineHint      guifg=NONE      guibg=NONE   gui=undercurl   guisp=#767676

hi DiagnosticVirtualTextError   guifg=#ff3333   guibg=NONE   gui=italic
hi DiagnosticVirtualTextWarn    guifg=#f1ac00   guibg=NONE   gui=italic
hi DiagnosticVirtualTextInfo    guifg=#387af2   guibg=NONE   gui=italic
hi DiagnosticVirtualTextHint    guifg=#767676   guibg=NONE   gui=italic

hi DiagnosticSignError          guifg=#ff3333   guibg=NONE   gui=NONE
hi DiagnosticSignWarn           guifg=#f1ac00   guibg=NONE   gui=NONE
hi DiagnosticSignInfo           guifg=#387af2   guibg=NONE   gui=NONE
hi DiagnosticSignHint           guifg=#767676   guibg=NONE   gui=NONE

hi DiagnosticFloatingError      guifg=#ff3333   guibg=#111820 gui=NONE
hi DiagnosticFloatingWarn       guifg=#f1ac00   guibg=#111820 gui=NONE
hi DiagnosticFloatingInfo       guifg=#387af2   guibg=#111820 gui=NONE
hi DiagnosticFloatingHint       guifg=#767676   guibg=#111820 gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Syntax — base groups
" ─────────────────────────────────────────────────────────────────────────────
" Comments: #767676 italic (4.62:1 on bg).
" Previous value #555555 was 2.82:1 — fatally low for 10h+ coding sessions.  [FIX v2]
hi Comment         guifg=#767676   guibg=NONE   gui=italic

hi Constant        guifg=#4affc4   guibg=NONE   gui=NONE
hi String          guifg=#f1ac00   guibg=NONE   gui=NONE
hi Character       guifg=#f1ac00   guibg=NONE   gui=NONE
hi Number          guifg=#4affc4   guibg=NONE   gui=NONE
" Boolean linked to Keyword (blue, bold) — booleans are keyword-class tokens,
" not error/warning values. Using bright-red (#ff4444) created false urgency.  [FIX v2]
hi Boolean         guifg=#387af2   guibg=NONE   gui=bold
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
" SpecialComment bumped to #767676 bold.  [FIX v2]
hi SpecialComment  guifg=#767676   guibg=NONE   gui=bold
hi Debug           guifg=#ff4444   guibg=NONE   gui=NONE

hi Underlined      guifg=NONE      guibg=NONE   gui=underline
hi Ignore          guifg=#333333   guibg=NONE   gui=NONE
" Error uses softened red.  [FIX v2]
hi Error           guifg=#ff3333   guibg=NONE   gui=bold
hi Todo            guifg=#000000   guibg=#f1ac00 gui=bold

" ─────────────────────────────────────────────────────────────────────────────
" Misc UI
" ─────────────────────────────────────────────────────────────────────────────
hi Title           guifg=#387af2   guibg=NONE   gui=bold
hi Directory       guifg=#387af2   guibg=NONE   gui=bold
hi WildMenu        guifg=#000000   guibg=#387af2 gui=bold
hi QuickFixLine    guifg=NONE      guibg=#1a2d4a gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Treesitter — explicit @-namespace groups (Neovim 0.8+ parser highlights)
" ─────────────────────────────────────────────────────────────────────────────
" Comments
hi! link @comment            Comment
" Documentation comments (#8a8a8a, 6.08:1) — brighter than code comments to
" signal they carry API/interface meaning.  [FIX v2: new group]
hi   @comment.documentation  guifg=#8a8a8a   guibg=NONE   gui=italic

" Literals
hi! link @string             String
hi! link @string.escape      SpecialChar
hi! link @string.special     SpecialChar
hi! link @string.regex       guifg=#44ddff guibg=NONE gui=NONE
hi   @string.regexp          guifg=#44ddff   guibg=NONE   gui=NONE
hi! link @number             Number
hi! link @float              Float
hi! link @boolean            Boolean
hi! link @character          Character
hi! link @character.special  SpecialChar

" Variables
hi! link @variable           Identifier
" Function parameters: italic white — visually distinct from plain locals
" without introducing an extra color.  [FIX v2: new group]
hi   @variable.parameter     guifg=#ffffff   guibg=NONE   gui=italic
hi! link @variable.builtin   Special
hi! link @variable.member    @property
" Object/struct properties: light blue-tinted white (#c8d8f8, 14.63:1).
" Distinct from plain Identifier while staying within the blue-tinted palette.  [FIX v2: new group]
hi   @property               guifg=#c8d8f8   guibg=NONE   gui=NONE

" Functions
hi! link @function           Function
hi! link @function.builtin   Special
hi! link @function.macro     Macro
hi! link @function.call      Function
hi! link @method             Function
hi! link @method.call        Function
hi! link @constructor        Function

" Types
hi! link @type               Type
hi! link @type.builtin       Type
hi! link @type.qualifier     StorageClass
hi! link @type.definition    Typedef

" Keywords
hi! link @keyword            Keyword
hi! link @keyword.return     Keyword
hi! link @keyword.function   Keyword
hi! link @keyword.operator   Operator
hi! link @keyword.import     Include
hi! link @keyword.type       Type
hi! link @keyword.modifier   StorageClass
hi! link @keyword.repeat     Repeat
hi! link @keyword.exception  Exception
hi! link @conditional        Conditional
hi! link @conditional.ternary Operator
hi! link @repeat             Repeat
hi! link @exception          Exception
hi! link @include            Include
hi! link @preproc            PreProc
hi! link @define             Define
hi! link @operator           Operator

" Punctuation
hi! link @punctuation.delimiter Delimiter
hi! link @punctuation.bracket   Delimiter
hi! link @punctuation.special   Special

" Constants / namespaces
hi! link @constant           Constant
hi! link @constant.builtin   Special
hi! link @constant.macro     Define
" Modules/namespaces: accent_hover blue, same family as Type but distinct role
hi   @module                 guifg=#4a8cf5   guibg=NONE   gui=NONE
hi! link @namespace          @module
hi! link @label              Label

" Markup / HTML / JSX
hi! link @tag                Tag
hi   @tag.attribute          guifg=#0aeea0   guibg=NONE   gui=NONE
hi! link @tag.delimiter      Delimiter
hi! link @markup.heading     Title
hi! link @markup.link        guifg=#01c1f1 guibg=NONE gui=underline
hi   @markup.link.url        guifg=#01c1f1   guibg=NONE   gui=underline
hi! link @markup.raw         String
hi! link @markup.strong      gui=bold
hi! link @markup.italic      gui=italic

" Diff (Treesitter diff parser)
hi @diff.plus                guifg=#0aeea0   guibg=#001a0f   gui=NONE
hi @diff.minus               guifg=#ff3333   guibg=#1a0000   gui=NONE
hi @diff.delta               guifg=#f1ac00   guibg=#141000   gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" LSP Semantic Tokens (Neovim 0.9+ — takes priority over Treesitter)
" ─────────────────────────────────────────────────────────────────────────────
hi! link @lsp.type.class         Type
hi! link @lsp.type.interface     Type
hi! link @lsp.type.struct        Structure
hi! link @lsp.type.enum          Type
hi! link @lsp.type.enumMember    Constant
hi! link @lsp.type.function      Function
hi! link @lsp.type.method        Function
hi! link @lsp.type.macro         Macro
hi! link @lsp.type.variable      Identifier
hi! link @lsp.type.parameter     @variable.parameter
hi! link @lsp.type.property      @property
hi! link @lsp.type.namespace     @module
hi! link @lsp.type.keyword       Keyword
hi! link @lsp.type.comment       Comment
hi! link @lsp.type.string        String
hi! link @lsp.type.number        Number
hi! link @lsp.type.operator      Operator
hi! link @lsp.type.decorator     PreProc
hi! link @lsp.type.type          Type
hi! link @lsp.type.typeParameter Type
hi! link @lsp.type.event         Special
hi! link @lsp.type.regexp        @string.regexp
" Deprecated symbols: strikethrough over normal color
hi @lsp.mod.deprecated       gui=strikethrough
hi @lsp.mod.readonly         gui=italic

" ─────────────────────────────────────────────────────────────────────────────
" Plugin highlights
" ─────────────────────────────────────────────────────────────────────────────

" ── Telescope ──────────────────────────────────────────────────────────────
hi! link TelescopeNormal         NormalFloat
hi! link TelescopePreviewNormal  NormalFloat
hi   TelescopeBorder             guifg=#387af2   guibg=#111820   gui=NONE
hi! link TelescopePromptBorder   TelescopeBorder
hi! link TelescopeResultsBorder  TelescopeBorder
hi! link TelescopePreviewBorder  TelescopeBorder
hi   TelescopeTitle              guifg=#387af2   guibg=#111820   gui=bold
hi! link TelescopePromptTitle    TelescopeTitle
hi! link TelescopeResultsTitle   TelescopeTitle
hi! link TelescopePreviewTitle   TelescopeTitle
hi   TelescopePromptPrefix       guifg=#387af2   guibg=NONE      gui=bold
hi   TelescopeSelectionCaret     guifg=#387af2   guibg=#1a2d4a   gui=NONE
hi   TelescopeSelection          guifg=#ffffff   guibg=#1a2d4a   gui=NONE
hi   TelescopeMultiSelection     guifg=#4a8cf5   guibg=#1a2d4a   gui=NONE
hi   TelescopeMatching           guifg=#f1ac00   guibg=NONE      gui=bold
hi   TelescopePromptCounter      guifg=#767676   guibg=NONE      gui=NONE

" ── nvim-tree ──────────────────────────────────────────────────────────────
hi   NvimTreeNormal              guifg=#ffffff   guibg=NONE      gui=NONE
hi   NvimTreeRootFolder          guifg=#387af2   guibg=NONE      gui=bold
hi   NvimTreeFolderIcon          guifg=#387af2   guibg=NONE      gui=NONE
hi   NvimTreeFolderName          guifg=#4a8cf5   guibg=NONE      gui=NONE
hi   NvimTreeOpenedFolderName    guifg=#ffffff   guibg=NONE      gui=bold
hi   NvimTreeEmptyFolderName     guifg=#767676   guibg=NONE      gui=italic
hi   NvimTreeIndentMarker        guifg=#333333   guibg=NONE      gui=NONE
hi   NvimTreeSymlink             guifg=#01c1f1   guibg=NONE      gui=underline
hi   NvimTreeExecFile            guifg=#0aeea0   guibg=NONE      gui=bold
hi   NvimTreeSpecialFile         guifg=#c678dd   guibg=NONE      gui=underline
hi   NvimTreeImageFile           guifg=#c678dd   guibg=NONE      gui=NONE
hi   NvimTreeGitDirty            guifg=#f1ac00   guibg=NONE      gui=NONE
hi   NvimTreeGitStaged           guifg=#0aeea0   guibg=NONE      gui=NONE
hi   NvimTreeGitNew              guifg=#0aeea0   guibg=NONE      gui=NONE
hi   NvimTreeGitDeleted          guifg=#ff3333   guibg=NONE      gui=NONE
hi   NvimTreeGitIgnored          guifg=#767676   guibg=NONE      gui=italic
hi   NvimTreeWinSeparator        guifg=#333333   guibg=NONE      gui=NONE
hi! link NvimTreeCursorLine      CursorLine
hi! link NvimTreeEndOfBuffer     EndOfBuffer

" ── neo-tree ───────────────────────────────────────────────────────────────
hi   NeoTreeNormal               guifg=#ffffff   guibg=NONE      gui=NONE
hi   NeoTreeNormalNC             guifg=#767676   guibg=NONE      gui=NONE
hi   NeoTreeRootName             guifg=#387af2   guibg=NONE      gui=bold
hi   NeoTreeDirectoryName        guifg=#4a8cf5   guibg=NONE      gui=NONE
hi   NeoTreeDirectoryIcon        guifg=#387af2   guibg=NONE      gui=NONE
hi   NeoTreeSymbolicLinkTarget   guifg=#01c1f1   guibg=NONE      gui=underline
hi   NeoTreeGitModified          guifg=#f1ac00   guibg=NONE      gui=NONE
hi   NeoTreeGitAdded             guifg=#0aeea0   guibg=NONE      gui=NONE
hi   NeoTreeGitDeleted           guifg=#ff3333   guibg=NONE      gui=NONE
hi   NeoTreeGitConflict          guifg=#ff4444   guibg=NONE      gui=bold
hi   NeoTreeGitIgnored           guifg=#767676   guibg=NONE      gui=italic
hi! link NeoTreeCursorLine       CursorLine
hi! link NeoTreeWinSeparator     WinSeparator
hi! link NeoTreeFloatBorder      FloatBorder
hi! link NeoTreeFloatTitle       FloatTitle

" ── GitSigns ───────────────────────────────────────────────────────────────
hi   GitSignsAdd                 guifg=#0aeea0   guibg=NONE      gui=NONE
hi   GitSignsChange              guifg=#f1ac00   guibg=NONE      gui=NONE
hi   GitSignsDelete              guifg=#ff3333   guibg=NONE      gui=NONE
hi   GitSignsAddNr               guifg=#0aeea0   guibg=NONE      gui=NONE
hi   GitSignsChangeNr            guifg=#f1ac00   guibg=NONE      gui=NONE
hi   GitSignsDeleteNr            guifg=#ff3333   guibg=NONE      gui=NONE
hi   GitSignsAddLn               guifg=NONE      guibg=#001a0f   gui=NONE
hi   GitSignsChangeLn            guifg=NONE      guibg=#141000   gui=NONE
hi   GitSignsDeleteLn            guifg=NONE      guibg=#1a0000   gui=NONE
hi   GitSignsCurrentLineBlame    guifg=#767676   guibg=NONE      gui=italic

" ── Trouble (diagnostics list) ─────────────────────────────────────────────
hi   TroubleNormal               guifg=#ffffff   guibg=NONE      gui=NONE
hi! link TroubleError            DiagnosticError
hi! link TroubleWarning          DiagnosticWarn
hi! link TroubleInfo             DiagnosticInfo
hi! link TroubleHint             DiagnosticHint
hi   TroubleLocation             guifg=#767676   guibg=NONE      gui=NONE
hi   TroubleFile                 guifg=#4a8cf5   guibg=NONE      gui=bold
hi   TroubleFoldIcon             guifg=#387af2   guibg=NONE      gui=NONE
hi! link TroubleIndent           Delimiter
hi! link TroubleCount            DiagnosticError

" ── WhichKey ───────────────────────────────────────────────────────────────
hi   WhichKey                    guifg=#387af2   guibg=NONE      gui=bold
hi   WhichKeyGroup               guifg=#0aeea0   guibg=NONE      gui=NONE
hi   WhichKeyDesc                guifg=#ffffff   guibg=NONE      gui=NONE
hi   WhichKeySeparator           guifg=#767676   guibg=NONE      gui=NONE
hi   WhichKeyValue               guifg=#767676   guibg=NONE      gui=italic
hi! link WhichKeyFloat           NormalFloat
hi! link WhichKeyBorder          FloatBorder

" ── indent-blankline (ibl) ─────────────────────────────────────────────────
hi   IblIndent                   guifg=#1a1a1a   guibg=NONE      gui=nocombine
hi   IblScope                    guifg=#333333   guibg=NONE      gui=nocombine
hi   IblWhitespace               guifg=#1a1a1a   guibg=NONE      gui=nocombine
" Legacy (indent-blankline v2)
hi! link IndentBlanklineChar     IblIndent
hi! link IndentBlanklineContextChar IblScope

" ── nvim-cmp ───────────────────────────────────────────────────────────────
hi! link CmpItemAbbr             Identifier
hi! link CmpItemAbbrMatch        TelescopeMatching
hi! link CmpItemAbbrMatchFuzzy   TelescopeMatching
hi! link CmpItemAbbrDeprecated   @lsp.mod.deprecated
hi   CmpItemKindText             guifg=#ffffff   guibg=NONE   gui=NONE
hi   CmpItemKindMethod           guifg=#0aeea0   guibg=NONE   gui=NONE
hi! link CmpItemKindFunction     CmpItemKindMethod
hi! link CmpItemKindConstructor  CmpItemKindMethod
hi   CmpItemKindField            guifg=#c8d8f8   guibg=NONE   gui=NONE
hi! link CmpItemKindProperty     CmpItemKindField
hi! link CmpItemKindVariable     Identifier
hi   CmpItemKindClass            guifg=#4a8cf5   guibg=NONE   gui=NONE
hi! link CmpItemKindInterface    CmpItemKindClass
hi! link CmpItemKindStruct       CmpItemKindClass
hi! link CmpItemKindModule       @module
hi   CmpItemKindKeyword          guifg=#387af2   guibg=NONE   gui=NONE
hi! link CmpItemKindEnumMember   Constant
hi! link CmpItemKindConstant     Constant
hi   CmpItemKindSnippet          guifg=#c678dd   guibg=NONE   gui=NONE
hi   CmpItemKindOperator         guifg=#01c1f1   guibg=NONE   gui=NONE
hi! link CmpItemKindTypeParameter Type
hi   CmpItemMenu                 guifg=#767676   guibg=NONE   gui=italic

" ── Noice (UI replacement) ─────────────────────────────────────────────────
hi! link NoiceCmdlinePopup       NormalFloat
hi! link NoiceCmdlinePopupBorder FloatBorder
hi! link NoiceCmdlineIcon        Title
hi! link NoiceConfirmBorder      FloatBorder
hi   NoiceCompletionItemKindDefault guifg=#767676 guibg=NONE gui=NONE

" ── Mason ──────────────────────────────────────────────────────────────────
hi! link MasonNormal             NormalFloat
hi! link MasonHighlight          Title
hi   MasonHighlightBlock         guifg=#000000   guibg=#387af2   gui=bold
hi   MasonMuted                  guifg=#767676   guibg=NONE      gui=NONE
hi   MasonError                  guifg=#ff3333   guibg=NONE      gui=bold
hi   MasonWarning                guifg=#f1ac00   guibg=NONE      gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" vim-airline (theme selector)
" ─────────────────────────────────────────────────────────────────────────────
" The airline theme file (autoload/airline/themes/adwaita_amoled.vim)
" must be on runtimepath. If absent, 'dark' is a acceptable fallback.
let g:airline_theme = 'adwaita_amoled'

" =============================================================================
" vim: ft=vim sw=4 ts=4 et
