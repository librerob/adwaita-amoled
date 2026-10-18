" =============================================================================
" adwaita-amoled.vim — Neovim colorscheme  (readability palette)
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
" Readability palette (2026-10-16)
" Text accent #dcc1ef; filled controls retain #9a4fd0 with white text.
" Ordinary text is checked across normal, float, selection and cursor-line
" backgrounds; separators and indentation guides use the non-text target.
" See COLOR_READABILITY.md for measured pairs, exceptions and limits.
" =============================================================================

" ─────────────────────────────────────────────────────────────────────────────
" Editor chrome
" ─────────────────────────────────────────────────────────────────────────────
hi Normal          guifg=#ffffff   guibg=#000000      gui=NONE
hi NormalNC        guifg=#c0c0c0   guibg=#000000      gui=NONE

" Float bg is blue-tinted dark (#1e1326) — distinguishable from both bg
" (#000000) and surface_card (#0f0f0f) without breaking the AMOLED aesthetic.
hi NormalFloat     guifg=#ffffff   guibg=#1e1326   gui=NONE
hi FloatBorder     guifg=#dcc1ef   guibg=#1e1326   gui=NONE
hi FloatTitle      guifg=#dcc1ef   guibg=#1e1326   gui=bold

hi LineNr          guifg=#a0a0a0   guibg=NONE      gui=NONE
hi CursorLineNr    guifg=#f1ac00   guibg=NONE      gui=bold
" Cursor-line and selected text use distinct dark blue-tinted surfaces.
hi CursorLine      guifg=NONE      guibg=#201529   gui=NONE
hi ColorColumn     guifg=NONE      guibg=#0f0f0f   gui=NONE

" SignColumn / FoldColumn — brought to #a0a0a0 for readability.
hi SignColumn      guifg=#a0a0a0   guibg=NONE      gui=NONE
hi FoldColumn      guifg=#a0a0a0   guibg=NONE      gui=NONE
hi Folded          guifg=#a0a0a0   guibg=#0f0f0f   gui=italic

hi EndOfBuffer     guifg=#333333   guibg=NONE      gui=NONE
hi NonText         guifg=#a0a0a0   guibg=NONE      gui=NONE
hi Whitespace      guifg=#a0a0a0   guibg=NONE      gui=NONE
hi SpecialKey      guifg=#a0a0a0   guibg=NONE      gui=NONE
hi Conceal         guifg=#a0a0a0   guibg=NONE      gui=NONE

" Identifying separators use #808080; decorative end-of-buffer tildes stay dim.
hi WinSeparator    guifg=#808080   guibg=NONE      gui=NONE
hi VertSplit       guifg=#808080   guibg=NONE      gui=NONE

" Window bar (breadcrumbs — Neovim 0.8+)
hi WinBar          guifg=#c0c0c0   guibg=NONE      gui=bold
hi WinBarNC        guifg=#a0a0a0   guibg=NONE      gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Status / tab line
" ─────────────────────────────────────────────────────────────────────────────
hi StatusLine      guifg=#c0c0c0   guibg=#0f0f0f   gui=NONE
" Secondary text remains readable on raised surfaces.
hi StatusLineNC    guifg=#a0a0a0   guibg=#0f0f0f   gui=NONE
hi TabLine         guifg=#a0a0a0   guibg=#0f0f0f   gui=NONE
hi TabLineSel      guifg=#ffffff   guibg=NONE      gui=bold
hi TabLineFill     guifg=NONE      guibg=#0f0f0f   gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Selection / search
" ─────────────────────────────────────────────────────────────────────────────
" Selection keeps ordinary text readable on the dark blue-tinted surface.
hi Visual          guifg=NONE      guibg=#392547   gui=NONE
hi VisualNOS       guifg=NONE      guibg=#392547   gui=NONE

" Search matches use black text on warning yellow.

hi Search          guifg=#000000   guibg=#f1ac00   gui=bold
" The current match uses black text on the pale blue accent.
hi IncSearch       guifg=#000000   guibg=#dcc1ef   gui=bold
hi CurSearch       guifg=#000000   guibg=#dcc1ef   gui=bold

hi MatchParen      guifg=#f1ac00   guibg=NONE      gui=bold,underline

" ─────────────────────────────────────────────────────────────────────────────
" Substitution preview (:s///)
" ─────────────────────────────────────────────────────────────────────────────
hi Substitute      guifg=#000000   guibg=#f1ac00   gui=bold

" ─────────────────────────────────────────────────────────────────────────────
" Popup / completion menu
" ─────────────────────────────────────────────────────────────────────────────
hi Pmenu           guifg=#ffffff   guibg=#1e1326   gui=NONE
hi PmenuSel        guifg=#000000   guibg=#dcc1ef   gui=bold
hi PmenuSbar       guifg=NONE      guibg=#1a1a1a   gui=NONE
hi PmenuThumb      guifg=NONE      guibg=#dcc1ef   gui=NONE
hi PmenuMatch      guifg=#f1ac00   guibg=#1e1326   gui=bold
hi PmenuMatchSel   guifg=#000000   guibg=#dcc1ef   gui=bold,underline

" ─────────────────────────────────────────────────────────────────────────────
" Messages & prompts
" ─────────────────────────────────────────────────────────────────────────────
" ErrorMsg uses softened error red.
hi ErrorMsg        guifg=#ff7b7b   guibg=NONE      gui=bold
hi WarningMsg      guifg=#f1ac00   guibg=NONE      gui=NONE
hi ModeMsg         guifg=#0aeea0   guibg=NONE      gui=bold
hi MsgArea         guifg=#c0c0c0   guibg=NONE      gui=NONE
hi MsgSeparator    guifg=#808080   guibg=NONE      gui=NONE
hi MoreMsg         guifg=#0aeea0   guibg=NONE      gui=bold
hi Question        guifg=#0aeea0   guibg=NONE      gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Diff
" ─────────────────────────────────────────────────────────────────────────────
hi DiffAdd         guifg=#0aeea0   guibg=#001a0f   gui=NONE
hi DiffChange      guifg=#f1ac00   guibg=#141000   gui=NONE
hi DiffDelete      guifg=#ff7b7b   guibg=#1a0000   gui=NONE
hi DiffText        guifg=#000000   guibg=#dcc1ef   gui=bold

" ─────────────────────────────────────────────────────────────────────────────
" Spell
" ─────────────────────────────────────────────────────────────────────────────
hi SpellBad        guifg=NONE      guibg=NONE      gui=undercurl   guisp=#ff7b7b
hi SpellCap        guifg=NONE      guibg=NONE      gui=undercurl   guisp=#f1ac00
hi SpellRare       guifg=NONE      guibg=NONE      gui=undercurl   guisp=#d49bea
hi SpellLocal      guifg=NONE      guibg=NONE      gui=undercurl   guisp=#01c1f1

" ─────────────────────────────────────────────────────────────────────────────
" Diagnostics (LSP / nvim-lsp)
" ─────────────────────────────────────────────────────────────────────────────
" Error uses softened #ff7b7b.
hi DiagnosticError              guifg=#ff7b7b   guibg=NONE   gui=NONE
hi DiagnosticWarn               guifg=#f1ac00   guibg=NONE   gui=NONE
hi DiagnosticInfo               guifg=#dcc1ef   guibg=NONE   gui=NONE
" Hints use readable secondary text, including inside floating windows.
hi DiagnosticHint               guifg=#a0a0a0   guibg=NONE   gui=NONE
hi DiagnosticOk                 guifg=#0aeea0   guibg=NONE   gui=NONE

hi DiagnosticUnderlineError     guifg=NONE      guibg=NONE   gui=undercurl   guisp=#ff7b7b
hi DiagnosticUnderlineWarn      guifg=NONE      guibg=NONE   gui=undercurl   guisp=#f1ac00
hi DiagnosticUnderlineInfo      guifg=NONE      guibg=NONE   gui=undercurl   guisp=#dcc1ef
" Hint squiggle bumped to #a0a0a0.
hi DiagnosticUnderlineHint      guifg=NONE      guibg=NONE   gui=undercurl   guisp=#a0a0a0

hi DiagnosticVirtualTextError   guifg=#ff7b7b   guibg=NONE   gui=italic
hi DiagnosticVirtualTextWarn    guifg=#f1ac00   guibg=NONE   gui=italic
hi DiagnosticVirtualTextInfo    guifg=#dcc1ef   guibg=NONE   gui=italic
hi DiagnosticVirtualTextHint    guifg=#a0a0a0   guibg=NONE   gui=italic

hi DiagnosticSignError          guifg=#ff7b7b   guibg=NONE   gui=NONE
hi DiagnosticSignWarn           guifg=#f1ac00   guibg=NONE   gui=NONE
hi DiagnosticSignInfo           guifg=#dcc1ef   guibg=NONE   gui=NONE
hi DiagnosticSignHint           guifg=#a0a0a0   guibg=NONE   gui=NONE

hi DiagnosticFloatingError      guifg=#ff7b7b   guibg=#1e1326 gui=NONE
hi DiagnosticFloatingWarn       guifg=#f1ac00   guibg=#1e1326 gui=NONE
hi DiagnosticFloatingInfo       guifg=#dcc1ef   guibg=#1e1326 gui=NONE
hi DiagnosticFloatingHint       guifg=#a0a0a0   guibg=#1e1326 gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Syntax — base groups
" ─────────────────────────────────────────────────────────────────────────────
" Comments use readable secondary text.
hi Comment         guifg=#a0a0a0   guibg=NONE   gui=italic

hi Constant        guifg=#4affc4   guibg=NONE   gui=NONE
hi String          guifg=#f1ac00   guibg=NONE   gui=NONE
hi Character       guifg=#f1ac00   guibg=NONE   gui=NONE
hi Number          guifg=#4affc4   guibg=NONE   gui=NONE
" Boolean linked to Keyword (blue, bold) — booleans are keyword-class tokens,
" not error/warning values. Using bright-red (#ff9a9a) created false urgency.
hi Boolean         guifg=#dcc1ef   guibg=NONE   gui=bold
hi Float           guifg=#4affc4   guibg=NONE   gui=NONE

hi Identifier      guifg=#ffffff   guibg=NONE   gui=NONE
hi Function        guifg=#0aeea0   guibg=NONE   gui=bold

hi Statement       guifg=#dcc1ef   guibg=NONE   gui=bold
hi Conditional     guifg=#dcc1ef   guibg=NONE   gui=bold
hi Repeat          guifg=#dcc1ef   guibg=NONE   gui=bold
hi Label           guifg=#e9dcf3   guibg=NONE   gui=NONE
hi Operator        guifg=#01c1f1   guibg=NONE   gui=NONE
hi Keyword         guifg=#dcc1ef   guibg=NONE   gui=bold
hi Exception       guifg=#ff9a9a   guibg=NONE   gui=bold

hi PreProc         guifg=#d49bea   guibg=NONE   gui=NONE
hi Include         guifg=#d49bea   guibg=NONE   gui=NONE
hi Define          guifg=#d49bea   guibg=NONE   gui=NONE
hi Macro           guifg=#e599ff   guibg=NONE   gui=NONE
hi PreCondit       guifg=#d49bea   guibg=NONE   gui=NONE

hi Type            guifg=#e9dcf3   guibg=NONE   gui=bold
hi StorageClass    guifg=#e9dcf3   guibg=NONE   gui=NONE
hi Structure       guifg=#e9dcf3   guibg=NONE   gui=NONE
hi Typedef         guifg=#e9dcf3   guibg=NONE   gui=NONE

hi Special         guifg=#01c1f1   guibg=NONE   gui=NONE
hi SpecialChar     guifg=#44ddff   guibg=NONE   gui=NONE
hi Tag             guifg=#dcc1ef   guibg=NONE   gui=NONE
hi Delimiter       guifg=#c0c0c0   guibg=NONE   gui=NONE
" SpecialComment bumped to #a0a0a0 bold.
hi SpecialComment  guifg=#a0a0a0   guibg=NONE   gui=bold
hi Debug           guifg=#ff9a9a   guibg=NONE   gui=NONE

hi Underlined      guifg=NONE      guibg=NONE   gui=underline
hi Ignore          guifg=#a0a0a0   guibg=NONE   gui=NONE
" Error uses softened red.
hi Error           guifg=#ff7b7b   guibg=NONE   gui=bold
hi Todo            guifg=#000000   guibg=#f1ac00 gui=bold

" ─────────────────────────────────────────────────────────────────────────────
" Misc UI
" ─────────────────────────────────────────────────────────────────────────────
hi Title           guifg=#dcc1ef   guibg=NONE   gui=bold
hi Directory       guifg=#dcc1ef   guibg=NONE   gui=bold
hi WildMenu        guifg=#000000   guibg=#dcc1ef gui=bold
hi QuickFixLine    guifg=NONE      guibg=#392547 gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" Treesitter — explicit @-namespace groups (Neovim 0.8+ parser highlights)
" ─────────────────────────────────────────────────────────────────────────────
" Comments
hi! link @comment            Comment
" Documentation comments are brighter than ordinary comments to
" signal they carry API/interface meaning.
hi   @comment.documentation  guifg=#b0b0b0   guibg=NONE   gui=italic

" Literals
hi! link @string             String
hi! link @string.escape      SpecialChar
hi! link @string.special     SpecialChar
hi   @string.regex       guifg=#44ddff guibg=NONE gui=NONE
hi   @string.regexp          guifg=#44ddff   guibg=NONE   gui=NONE
hi! link @number             Number
hi! link @float              Float
hi! link @boolean            Boolean
hi! link @character          Character
hi! link @character.special  SpecialChar

" Variables
hi! link @variable           Identifier
" Function parameters: italic white — visually distinct from plain locals
" without introducing an extra color.
hi   @variable.parameter     guifg=#ffffff   guibg=NONE   gui=italic
hi! link @variable.builtin   Special
hi! link @variable.member    @property
" Object/struct properties use light blue-tinted white.
" Distinct from plain Identifier while staying within the blue-tinted palette.
hi   @property               guifg=#e1d3eb   guibg=NONE   gui=NONE

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
hi   @module                 guifg=#e9dcf3   guibg=NONE   gui=NONE
hi! link @namespace          @module
hi! link @label              Label

" Markup / HTML / JSX
hi! link @tag                Tag
hi   @tag.attribute          guifg=#0aeea0   guibg=NONE   gui=NONE
hi! link @tag.delimiter      Delimiter
hi! link @markup.heading     Title
hi   @markup.link        guifg=#01c1f1 guibg=NONE gui=underline
hi   @markup.link.url        guifg=#01c1f1   guibg=NONE   gui=underline
hi! link @markup.raw         String
hi   @markup.strong      gui=bold
hi   @markup.italic      gui=italic

" Diff (Treesitter diff parser)
hi @diff.plus                guifg=#0aeea0   guibg=#001a0f   gui=NONE
hi @diff.minus               guifg=#ff7b7b   guibg=#1a0000   gui=NONE
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
hi   TelescopeBorder             guifg=#dcc1ef   guibg=#1e1326   gui=NONE
hi! link TelescopePromptBorder   TelescopeBorder
hi! link TelescopeResultsBorder  TelescopeBorder
hi! link TelescopePreviewBorder  TelescopeBorder
hi   TelescopeTitle              guifg=#dcc1ef   guibg=#1e1326   gui=bold
hi! link TelescopePromptTitle    TelescopeTitle
hi! link TelescopeResultsTitle   TelescopeTitle
hi! link TelescopePreviewTitle   TelescopeTitle
hi   TelescopePromptPrefix       guifg=#dcc1ef   guibg=NONE      gui=bold
hi   TelescopeSelectionCaret     guifg=#dcc1ef   guibg=#392547   gui=NONE
hi   TelescopeSelection          guifg=#ffffff   guibg=#392547   gui=NONE
hi   TelescopeMultiSelection     guifg=#e9dcf3   guibg=#392547   gui=NONE
hi   TelescopeMatching           guifg=#f1ac00   guibg=NONE      gui=bold
hi   TelescopePromptCounter      guifg=#a0a0a0   guibg=NONE      gui=NONE

" ── nvim-tree ──────────────────────────────────────────────────────────────
hi   NvimTreeNormal              guifg=#ffffff   guibg=NONE      gui=NONE
hi   NvimTreeRootFolder          guifg=#dcc1ef   guibg=NONE      gui=bold
hi   NvimTreeFolderIcon          guifg=#dcc1ef   guibg=NONE      gui=NONE
hi   NvimTreeFolderName          guifg=#e9dcf3   guibg=NONE      gui=NONE
hi   NvimTreeOpenedFolderName    guifg=#ffffff   guibg=NONE      gui=bold
hi   NvimTreeEmptyFolderName     guifg=#a0a0a0   guibg=NONE      gui=italic
hi   NvimTreeIndentMarker        guifg=#808080   guibg=NONE      gui=NONE
hi   NvimTreeSymlink             guifg=#01c1f1   guibg=NONE      gui=underline
hi   NvimTreeExecFile            guifg=#0aeea0   guibg=NONE      gui=bold
hi   NvimTreeSpecialFile         guifg=#d49bea   guibg=NONE      gui=underline
hi   NvimTreeImageFile           guifg=#d49bea   guibg=NONE      gui=NONE
hi   NvimTreeGitDirty            guifg=#f1ac00   guibg=NONE      gui=NONE
hi   NvimTreeGitStaged           guifg=#0aeea0   guibg=NONE      gui=NONE
hi   NvimTreeGitNew              guifg=#0aeea0   guibg=NONE      gui=NONE
hi   NvimTreeGitDeleted          guifg=#ff7b7b   guibg=NONE      gui=NONE
hi   NvimTreeGitIgnored          guifg=#a0a0a0   guibg=NONE      gui=italic
hi   NvimTreeWinSeparator        guifg=#808080   guibg=NONE      gui=NONE
hi! link NvimTreeCursorLine      CursorLine
hi! link NvimTreeEndOfBuffer     EndOfBuffer

" ── neo-tree ───────────────────────────────────────────────────────────────
hi   NeoTreeNormal               guifg=#ffffff   guibg=NONE      gui=NONE
hi   NeoTreeNormalNC             guifg=#a0a0a0   guibg=NONE      gui=NONE
hi   NeoTreeRootName             guifg=#dcc1ef   guibg=NONE      gui=bold
hi   NeoTreeDirectoryName        guifg=#e9dcf3   guibg=NONE      gui=NONE
hi   NeoTreeDirectoryIcon        guifg=#dcc1ef   guibg=NONE      gui=NONE
hi   NeoTreeSymbolicLinkTarget   guifg=#01c1f1   guibg=NONE      gui=underline
hi   NeoTreeGitModified          guifg=#f1ac00   guibg=NONE      gui=NONE
hi   NeoTreeGitAdded             guifg=#0aeea0   guibg=NONE      gui=NONE
hi   NeoTreeGitDeleted           guifg=#ff7b7b   guibg=NONE      gui=NONE
hi   NeoTreeGitConflict          guifg=#ff9a9a   guibg=NONE      gui=bold
hi   NeoTreeGitIgnored           guifg=#a0a0a0   guibg=NONE      gui=italic
hi! link NeoTreeCursorLine       CursorLine
hi! link NeoTreeWinSeparator     WinSeparator
hi! link NeoTreeFloatBorder      FloatBorder
hi! link NeoTreeFloatTitle       FloatTitle

" ── GitSigns ───────────────────────────────────────────────────────────────
hi   GitSignsAdd                 guifg=#0aeea0   guibg=NONE      gui=NONE
hi   GitSignsChange              guifg=#f1ac00   guibg=NONE      gui=NONE
hi   GitSignsDelete              guifg=#ff7b7b   guibg=NONE      gui=NONE
hi   GitSignsAddNr               guifg=#0aeea0   guibg=NONE      gui=NONE
hi   GitSignsChangeNr            guifg=#f1ac00   guibg=NONE      gui=NONE
hi   GitSignsDeleteNr            guifg=#ff7b7b   guibg=NONE      gui=NONE
hi   GitSignsAddLn               guifg=NONE      guibg=#001a0f   gui=NONE
hi   GitSignsChangeLn            guifg=NONE      guibg=#141000   gui=NONE
hi   GitSignsDeleteLn            guifg=NONE      guibg=#1a0000   gui=NONE
hi   GitSignsCurrentLineBlame    guifg=#a0a0a0   guibg=NONE      gui=italic

" ── Trouble (diagnostics list) ─────────────────────────────────────────────
hi   TroubleNormal               guifg=#ffffff   guibg=NONE      gui=NONE
hi! link TroubleError            DiagnosticError
hi! link TroubleWarning          DiagnosticWarn
hi! link TroubleInfo             DiagnosticInfo
hi! link TroubleHint             DiagnosticHint
hi   TroubleLocation             guifg=#a0a0a0   guibg=NONE      gui=NONE
hi   TroubleFile                 guifg=#e9dcf3   guibg=NONE      gui=bold
hi   TroubleFoldIcon             guifg=#dcc1ef   guibg=NONE      gui=NONE
hi! link TroubleIndent           Delimiter
hi! link TroubleCount            DiagnosticError

" ── WhichKey ───────────────────────────────────────────────────────────────
hi   WhichKey                    guifg=#dcc1ef   guibg=NONE      gui=bold
hi   WhichKeyGroup               guifg=#0aeea0   guibg=NONE      gui=NONE
hi   WhichKeyDesc                guifg=#ffffff   guibg=NONE      gui=NONE
hi   WhichKeySeparator           guifg=#a0a0a0   guibg=NONE      gui=NONE
hi   WhichKeyValue               guifg=#a0a0a0   guibg=NONE      gui=italic
hi! link WhichKeyFloat           NormalFloat
hi! link WhichKeyBorder          FloatBorder

" ── indent-blankline (ibl) ─────────────────────────────────────────────────
hi   IblIndent                   guifg=#808080   guibg=NONE      gui=nocombine
hi   IblScope                    guifg=#808080   guibg=NONE      gui=nocombine
hi   IblWhitespace               guifg=#808080   guibg=NONE      gui=nocombine
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
hi   CmpItemKindField            guifg=#e1d3eb   guibg=NONE   gui=NONE
hi! link CmpItemKindProperty     CmpItemKindField
hi! link CmpItemKindVariable     Identifier
hi   CmpItemKindClass            guifg=#e9dcf3   guibg=NONE   gui=NONE
hi! link CmpItemKindInterface    CmpItemKindClass
hi! link CmpItemKindStruct       CmpItemKindClass
hi! link CmpItemKindModule       @module
hi   CmpItemKindKeyword          guifg=#dcc1ef   guibg=NONE   gui=NONE
hi! link CmpItemKindEnumMember   Constant
hi! link CmpItemKindConstant     Constant
hi   CmpItemKindSnippet          guifg=#d49bea   guibg=NONE   gui=NONE
hi   CmpItemKindOperator         guifg=#01c1f1   guibg=NONE   gui=NONE
hi! link CmpItemKindTypeParameter Type
hi   CmpItemMenu                 guifg=#a0a0a0   guibg=NONE   gui=italic

" ── Noice (UI replacement) ─────────────────────────────────────────────────
hi! link NoiceCmdlinePopup       NormalFloat
hi! link NoiceCmdlinePopupBorder FloatBorder
hi! link NoiceCmdlineIcon        Title
hi! link NoiceConfirmBorder      FloatBorder
hi   NoiceCompletionItemKindDefault guifg=#a0a0a0 guibg=NONE gui=NONE

" ── Mason ──────────────────────────────────────────────────────────────────
hi! link MasonNormal             NormalFloat
hi! link MasonHighlight          Title
hi   MasonHighlightBlock         guifg=#000000   guibg=#dcc1ef   gui=bold
hi   MasonMuted                  guifg=#a0a0a0   guibg=NONE      gui=NONE
hi   MasonError                  guifg=#ff7b7b   guibg=NONE      gui=bold
hi   MasonWarning                guifg=#f1ac00   guibg=NONE      gui=NONE

" ─────────────────────────────────────────────────────────────────────────────
" vim-airline (theme selector)
" ─────────────────────────────────────────────────────────────────────────────
" The airline theme file (autoload/airline/themes/adwaita_amoled.vim)
" must be on runtimepath. If absent, 'dark' is an acceptable fallback.
let g:airline_theme = 'adwaita_amoled'

" =============================================================================
" vim: ft=vim sw=4 ts=4 et
