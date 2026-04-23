" =============================================================================
" autoload/airline/themes/adwaita_amoled.vim
" vim-airline theme for Adwaita-AMOLED
" =============================================================================
"
" Palette columns: [ guifg, guibg, ctermfg, ctermbg ]
"
"   normal mode   → accent blue  #387af2 on surface_card #0f0f0f
"   insert mode   → black        #000000 on success      #0aeea0
"   visual mode   → black        #000000 on warning      #f1ac00
"   replace mode  → black        #000000 on error        #ff0000
"   inactive      → ghost        #555555 on surface_card #0f0f0f

let s:bg        = ['#000000', 0 ]
let s:surface   = ['#0f0f0f', 233]
let s:hover     = ['#1a1a1a', 234]
let s:border    = ['#2a2a2a', 235]
let s:ghost     = ['#555555', 240]
let s:disabled  = ['#c0c0c0', 251]
let s:fg        = ['#ffffff', 15 ]

let s:blue      = ['#387af2', 69 ]
let s:blue_h    = ['#4a8cf5', 69 ]
let s:green     = ['#0aeea0', 85 ]
let s:yellow    = ['#f1ac00', 214]
let s:red       = ['#ff0000', 196]
let s:magenta   = ['#c678dd', 176]
let s:cyan      = ['#01c1f1', 45 ]

let g:airline#themes#adwaita_amoled#palette = {}

" --- Normal mode -------------------------------------------------------------
let s:N1 = [s:bg[0],       s:blue[0],    s:bg[1],    s:blue[1]   ]  " mode block
let s:N2 = [s:disabled[0], s:hover[0],   s:disabled[1], s:hover[1]]  " middle sections
let s:N3 = [s:ghost[0],    s:surface[0], s:ghost[1], s:surface[1]]   " filename / right

let g:airline#themes#adwaita_amoled#palette.normal =
    \ airline#themes#generate_color_map(s:N1, s:N2, s:N3)

let g:airline#themes#adwaita_amoled#palette.normal_modified = {
    \ 'airline_c': [s:yellow[0], s:surface[0], s:yellow[1], s:surface[1], ''],
    \ }

" --- Insert mode -------------------------------------------------------------
let s:I1 = [s:bg[0],       s:green[0],   s:bg[1],    s:green[1]  ]
let s:I2 = [s:disabled[0], s:hover[0],   s:disabled[1], s:hover[1]]
let s:I3 = [s:ghost[0],    s:surface[0], s:ghost[1], s:surface[1]]

let g:airline#themes#adwaita_amoled#palette.insert =
    \ airline#themes#generate_color_map(s:I1, s:I2, s:I3)

let g:airline#themes#adwaita_amoled#palette.insert_modified =
    \ g:airline#themes#adwaita_amoled#palette.normal_modified

" --- Visual mode -------------------------------------------------------------
let s:V1 = [s:bg[0],       s:yellow[0],  s:bg[1],    s:yellow[1] ]
let s:V2 = [s:disabled[0], s:hover[0],   s:disabled[1], s:hover[1]]
let s:V3 = [s:ghost[0],    s:surface[0], s:ghost[1], s:surface[1]]

let g:airline#themes#adwaita_amoled#palette.visual =
    \ airline#themes#generate_color_map(s:V1, s:V2, s:V3)

let g:airline#themes#adwaita_amoled#palette.visual_modified =
    \ g:airline#themes#adwaita_amoled#palette.normal_modified

" --- Replace mode ------------------------------------------------------------
let s:R1 = [s:bg[0],       s:red[0],     s:bg[1],    s:red[1]    ]
let s:R2 = [s:disabled[0], s:hover[0],   s:disabled[1], s:hover[1]]
let s:R3 = [s:ghost[0],    s:surface[0], s:ghost[1], s:surface[1]]

let g:airline#themes#adwaita_amoled#palette.replace =
    \ airline#themes#generate_color_map(s:R1, s:R2, s:R3)

let g:airline#themes#adwaita_amoled#palette.replace_modified =
    \ g:airline#themes#adwaita_amoled#palette.normal_modified

" --- Inactive windows --------------------------------------------------------
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

" =============================================================================
" vim: ft=vim sw=4 ts=4
