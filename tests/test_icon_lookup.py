"""Render installed folder presets via GTK3, GTK4, Qt5 and Qt6 icon lookup."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import test_installer as base
sys.path.insert(0, str(base.ROOT / "tools"))
import generate_palette as palette

NAMES = ("blue", "yellow", "gold", "purple", "green", "red", "orange", "pink")
FOLDERS = ("folder", "folder-open", "folder-documents", "folder-download",
           "folder-downloads", "folder-music", "folder-pictures", "folder-projects",
           "folder-publicshare", "folder-remote", "folder-templates", "folder-videos",
           "folder-bookmarks", "folder-drag-accept", "inode-directory",
           "user-desktop", "user-home", "user-bookmarks")


class IconLookupTests(unittest.TestCase):
    setUp = base.InstallerTests.setUp
    run_cli = base.InstallerTests.run_cli
    write = base.InstallerTests.write

    def test_every_preset_resolves_and_renders_in_gtk_and_qt(self):
        output = Path(os.environ.get("THEME_TEST_OUTPUT", self.base / "rendered"))
        output.mkdir(parents=True, exist_ok=True)
        for accent in NAMES:
            self.run_cli("--icons", "--accent", accent)
            root = self.data / "icons" / base.THEME
            hicolor = root.parent / "hicolor"
            self.write(hicolor / "index.theme", "[Icon Theme]\nName=hicolor\nDirectories=48x48/apps\n[48x48/apps]\nSize=48\nType=Fixed\nContext=Applications\n")
            self.write(hicolor / "48x48/apps/org.example.IconTest.svg", '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"><rect width="48" height="48" fill="#ffffff"/></svg>')
            env = dict(self.env, ICON_ROOT=str(root), ICON_NAMES=json.dumps(FOLDERS),
                       ICON_OUTPUT=str(output / accent), QT_QPA_PLATFORM="offscreen",
                       ICON_FACE=palette.preset_colors(base.ROOT, accent)["accent_text"])
            result = subprocess.run([sys.executable, "-c", GTK2], env=env,
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for toolkit in ("3.0", "4.0"):
                with self.subTest(accent=accent, gtk=toolkit):
                    result = subprocess.run([sys.executable, "-c", GTK, toolkit], env=env,
                                            capture_output=True, text=True, timeout=60)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for toolkit in ("5", "6"):
                with self.subTest(accent=accent, qt=toolkit):
                    result = subprocess.run([sys.executable, "-c", QT, toolkit], env=env,
                                            capture_output=True, text=True, timeout=60)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


GTK2 = r'''
import ctypes as C, ctypes.util, json, os
from pathlib import Path
gtk=C.CDLL(ctypes.util.find_library('gtk-x11-2.0'))
pix=C.CDLL(ctypes.util.find_library('gdk_pixbuf-2.0'))
obj=C.CDLL(ctypes.util.find_library('gobject-2.0'))
def signature(lib,name,result,args):
 f=getattr(lib,name);f.restype=result;f.argtypes=args;return f
init=signature(gtk,'gtk_init_check',C.c_int,[C.c_void_p,C.c_void_p])
assert init(None,None)
new=signature(gtk,'gtk_icon_theme_new',C.c_void_p,[])
paths=signature(gtk,'gtk_icon_theme_set_search_path',None,[C.c_void_p,C.POINTER(C.c_char_p),C.c_int])
get_paths=signature(gtk,'gtk_icon_theme_get_search_path',None,[C.c_void_p,C.POINTER(C.POINTER(C.c_char_p)),C.POINTER(C.c_int)])
custom=signature(gtk,'gtk_icon_theme_set_custom_theme',None,[C.c_void_p,C.c_char_p])
lookup=signature(gtk,'gtk_icon_theme_lookup_icon',C.c_void_p,[C.c_void_p,C.c_char_p,C.c_int,C.c_int])
filename=signature(gtk,'gtk_icon_info_get_filename',C.c_char_p,[C.c_void_p])
load=signature(gtk,'gtk_icon_info_load_icon',C.c_void_p,[C.c_void_p,C.c_void_p])
free=signature(gtk,'gtk_icon_info_free',None,[C.c_void_p])
unref=signature(obj,'g_object_unref',None,[C.c_void_p])
width=signature(pix,'gdk_pixbuf_get_width',C.c_int,[C.c_void_p])
theme=new();root=Path(os.environ['ICON_ROOT'])
defaults=C.POINTER(C.c_char_p)();count=C.c_int()
get_paths(theme,C.byref(defaults),C.byref(count))
assert str(root.parent) in [defaults[i].decode() for i in range(count.value)]
entries=[str(root.parent),'/usr/local/share/icons','/usr/share/icons','/usr/share/pixmaps']
array=(C.c_char_p*len(entries))(*(x.encode() for x in entries))
paths(theme,array,len(entries));custom(theme,b'Adwaita-AMOLED')
for name in json.loads(os.environ['ICON_NAMES']):
 for size in [16,20,24,32,48,64,128]:
  icon=lookup(theme,name.encode(),size,0);assert icon,(name,size)
  path=Path(filename(icon).decode());assert path.is_relative_to(root),(name,size,path)
  image=load(icon,None);assert image and width(image)>0,(name,size)
  unref(image);free(icon)
icon=lookup(theme,b'folder-symbolic',16,0)
assert icon and '/Adwaita/' in filename(icon).decode()
free(icon)
icon=lookup(theme,b'org.example.IconTest',48,0)
assert icon and '/hicolor/' in filename(icon).decode()
free(icon);unref(theme)
'''

GTK = r'''
import gi, json, os, sys
from pathlib import Path
version=sys.argv[1]
gi.require_version('Gtk', version)
from gi.repository import Gtk, Gdk
Gtk.init([]) if version == '3.0' else Gtk.init()
root=Path(os.environ['ICON_ROOT'])
paths=[str(root.parent),'/usr/local/share/icons','/usr/share/icons','/usr/share/pixmaps']
theme=Gtk.IconTheme.new()
assert str(root.parent) in theme.get_search_path(),theme.get_search_path()
theme.set_search_path(paths)
if version=='3.0': theme.set_custom_theme('Adwaita-AMOLED')
else: theme.set_theme_name('Adwaita-AMOLED')
for name in json.loads(os.environ['ICON_NAMES']):
 for size in [16,20,24,32,48,64,128]:
  for scale in [1,2]:
   if version=='3.0':
    icon=theme.lookup_icon_for_scale(name,size,scale,Gtk.IconLookupFlags.FORCE_REGULAR)
    assert icon, (name,size,scale)
    filename=icon.get_filename()
    image=icon.load_icon()
    assert image.get_width()>0 and any(image.get_pixels()[3::4]), (name,size)
    if size in (16,64) and scale==1:
     dest=Path(os.environ['ICON_OUTPUT']);dest.mkdir(parents=True,exist_ok=True)
     image.savev(str(dest/f'{name}-{size}.png'),'png',[],[])
   else:
    icon=theme.lookup_icon(name,None,size,scale,Gtk.TextDirection.LTR,Gtk.IconLookupFlags.FORCE_REGULAR)
    filename=icon.get_file().get_path()
   assert Path(filename).is_relative_to(root),(version,name,size,scale,filename)
fallback=theme.lookup_icon('folder-symbolic',16,0) if version=='3.0' else theme.lookup_icon('folder-symbolic',None,16,1,Gtk.TextDirection.LTR,0)
filename=fallback.get_filename() if version=='3.0' else fallback.get_file().get_path()
assert not Path(filename).is_relative_to(root),filename
assert '/Adwaita/' in filename, filename
app=theme.lookup_icon('org.example.IconTest',48,0) if version=='3.0' else theme.lookup_icon('org.example.IconTest',None,48,1,Gtk.TextDirection.LTR,0)
filename=app.get_filename() if version=='3.0' else app.get_file().get_path()
assert '/hicolor/' in filename, filename
'''

QT = r'''
import importlib,json,os,sys
from pathlib import Path
Gui=importlib.import_module('PyQt'+sys.argv[1]+'.QtGui')
app=Gui.QGuiApplication([])
root=Path(os.environ['ICON_ROOT'])
# The offscreen test platform has no desktop theme plugin or search paths.
# Supply the standard paths explicitly, while checking the XDG data location.
Core=importlib.import_module('PyQt'+sys.argv[1]+'.QtCore')
location=Core.QStandardPaths.StandardLocation.GenericDataLocation if sys.argv[1]=='6' else Core.QStandardPaths.GenericDataLocation
assert str(root.parent.parent) in Core.QStandardPaths.standardLocations(location)
Gui.QIcon.setThemeSearchPaths([str(root.parent),'/usr/local/share/icons','/usr/share/icons'])
Gui.QIcon.setThemeName('Adwaita-AMOLED')
for name in json.loads(os.environ['ICON_NAMES']):
 icon=Gui.QIcon.fromTheme(name)
 assert not icon.isNull(),name
 for size in [16,20,24,32,48,64,128]:
  pixmap=icon.pixmap(size,size)
  assert not pixmap.isNull(),(name,size)
  image=pixmap.toImage()
  assert any(image.pixelColor(x,y).alpha() for x in range(image.width()) for y in range(image.height())),(name,size)
  if name=='folder':
   face=image.pixelColor(image.width()//2,image.height()*3//4).name()
   assert face==os.environ['ICON_FACE'],('Qt SVG icon engine missing or wrong preset',name,size,face,os.environ['ICON_FACE'])
assert not Gui.QIcon.fromTheme('folder-symbolic').isNull()
assert not Gui.QIcon.fromTheme('org.example.IconTest').isNull()
'''


if __name__ == "__main__":
    unittest.main(verbosity=2)
