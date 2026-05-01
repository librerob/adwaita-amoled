" =============================================================================
" autoload/airline/themes/adwaita_amoled.vim
" vim-airline theme for Adwaita-AMOLED  (revised v2)
" =============================================================================
"
" Palette columns: [ guifg, guibg, ctermfg, ctermbg ]
"
"   normal mode   → black   #000000 on accent blue    #387af2
"   insert mode   → black   #000000 on success green  #0aeea0
"   visual mode   → black   #000000 on warning yellow #f1ac00
"   replace mode  → black   #000000 on error red      #ff3333  [FIX v2]
"   inactive      → #737373 on surface_card #0f0f0f   [FIX v2: was #555555 2.57:1]
"
" v2 changes:
"   • s:ghost  #555555 → #737373  (2.57:1 → 4.04:1 on surface_card)
"     Inactive statusline text was nearly unreadable on the surface_card
"     background. At 4.04:1 it's clearly legible as secondary/inactive.
"   • s:red    #ff0000 → #ff3333  (consistent with colorscheme error color)
"
" =============================================================================

let s:bg        = ['#000000', 0  ]
let s:surface   = ['#0f0f0f', 233]
let s:hover     = ['#1a1a1a', 234]
let s:border    = ['#333333', 236]
" ghost_ui: inactive text — bumped from #555555 (2.57:1) to #737373 (4.04:1)  [FIX v2]
let s:ghost     = ['#737373', 243]
let s:disabled  = ['#c0c0c0', 251]
let s:fg        = ['#ffffff', 15 ]

let s:blue      = ['#387af2', 69 ]
let s:blue_h    = ['#4a8cf5', 69 ]
let s:green     = ['#0aeea0', 85 ]
let s:yellow    = ['#f1ac00', 214]
" Softened error red consistent with colorscheme.  [FIX v2]
let s:red       = ['#ff3333', 196]
let s:magenta   = ['#c678dd', 176]
let s:cyan      = ['#01c1f1', 45 ]

let g:airline#themes#adwaita_amoled#palette = {}

" ── Normal mode ──────────────────────────────────────────────────────────────
" N1: mode block — black text on accent blue
let s:N1 = [s:bg[0],       s:blue[0],    s:bg[1],    s:blue[1]   ]
" N2: branch/filetype — disabled text on slightly elevated surface
let s:N2 = [s:disabled[0], s:hover[0],   s:disabled[1], s:hover[1]]
" N3: filename / right sections — ghost text on surface_card
let s:N3 = [s:ghost[0],    s:surface[0], s:ghost[1], s:surface[1]]

let g:airline#themes#adwaita_amoled#palette.normal =
    \ airline#themes#generate_color_map(s:N1, s:N2, s:N3)

" Modified buffer: filename section uses warning yellow
let g:airline#themes#adwaita_amoled#palette.normal_modified = {
    \ 'airline_c': [s:yellow[0], s:surface[0], s:yellow[1], s:surface[1], ''],
    \ }

" ── Insert mode ──────────────────────────────────────────────────────────────
let s:I1 = [s:bg[0],       s:green[0],   s:bg[1],    s:green[1]  ]
let s:I2 = [s:disabled[0], s:hover[0],   s:disabled[1], s:hover[1]]
let s:I3 = [s:ghost[0],    s:surface[0], s:ghost[1], s:surface[1]]

let g:airline#themes#adwaita_amoled#palette.insert =
    \ airline#themes#generate_color_map(s:I1, s:I2, s:I3)

let g:airline#themes#adwaita_amoled#palette.insert_modified =
    \ g:airline#themes#adwaita_amoled#palette.normal_modified

" ── Visual mode ──────────────────────────────────────────────────────────────
let s:V1 = [s:bg[0],       s:yellow[0],  s:bg[1],    s:yellow[1] ]
let s:V2 = [s:disabled[0], s:hover[0],   s:disabled[1], s:hover[1]]
let s:V3 = [s:ghost[0],    s:surface[0], s:ghost[1], s:surface[1]]

let g:airline#themes#adwaita_amoled#palette.visual =
    \ airline#themes#generate_color_map(s:V1, s:V2, s:V3)

let g:airline#themes#adwaita_amoled#palette.visual_modified =
    \ g:airline#themes#adwaita_amoled#palette.normal_modified

" ── Replace mode ─────────────────────────────────────────────────────────────
" Uses softened error red #ff3333 — consistent with rest of theme.  [FIX v2]
let s:R1 = [s:bg[0],       s:red[0],     s:bg[1],    s:red[1]    ]
let s:R2 = [s:disabled[0], s:hover[0],   s:disabled[1], s:hover[1]]
let s:R3 = [s:ghost[0],    s:surface[0], s:ghost[1], s:surface[1]]

let g:airline#themes#adwaita_amoled#palette.replace =
    \ airline#themes#generate_color_map(s:R1, s:R2, s:R3)

let g:airline#themes#adwaita_amoled#palette.replace_modified =
    \ g:airline#themes#adwaita_amoled#palette.normal_modified

" ── Inactive windows ─────────────────────────────────────────────────────────
" All sections use ghost (#737373) on surface_card — 4.04:1.  [FIX v2]
let s:IA = [s:ghost[0],  s:surface[0], s:ghost[1], s:surface[1], '']

let g:airline#themes#adwaita_amoled#palette.inactive = {
    \ 'airline_a': s:IA,
    \ 'airline_b': s:IA,
    \ 'airline_c': s:IA,
    \ 'airline_x': s:IA,
    \ 'airline_y': s:IA,
    \ 'airline_z': s:IA,
    \ }

let g:airline#themes#adwaita_amoled#palette.inactive_modified = {
    \ 'airline_c': [s:yellow[0], s:surface[0], s:yellow[1], s:surface[1], ''],
    \ }

" ── Accents (used by extensions: ale, coc, branch indicators, etc.) ──────────
" These are picked up automatically by extensions that call airline#themes#get_highlight
let g:airline#themes#adwaita_amoled#palette.accents = {
    \ 'red'    : [s:red[0],     '', s:red[1],     '', ''],
    \ 'green'  : [s:green[0],   '', s:green[1],   '', ''],
    \ 'yellow' : [s:yellow[0],  '', s:yellow[1],  '', ''],
    \ 'blue'   : [s:blue[0],    '', s:blue[1],    '', ''],
    \ 'magenta': [s:magenta[0], '', s:magenta[1], '', ''],
    \ 'cyan'   : [s:cyan[0],    '', s:cyan[1],    '', ''],
    \ 'white'  : [s:fg[0],      '', s:fg[1],      '', ''],
    \ }

" =============================================================================
" vim: ft=vim sw=4 ts=4 et
