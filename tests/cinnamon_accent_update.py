"""Live Cinnamon recoloring: run under fresh dbus-run-session and xvfb-run.

Requires Cinnamon/session, a system D-Bus service, GTK3 introspection and xdotool.
Uses a disposable HOME and the real installer; saves menu/calendar screenshots.
"""
import json,os,signal,subprocess,sys,tempfile,time
from pathlib import Path
import gi
gi.require_version('Gtk','3.0');from gi.repository import Gtk,Gdk,Gio,GLib
Gtk.init([])
ancestors=set();pid=os.getppid()
for _ in range(20):
 if pid<=1:break
 proc=Path('/proc')/str(pid);args=(proc/'cmdline').read_bytes().split(b'\0')
 ancestors.update(Path(os.fsdecode(arg)).name for arg in args[:3] if arg)
 pid=int(next(line.split()[1] for line in (proc/'status').read_text().splitlines() if line.startswith('PPid:')))
assert {'dbus-run-session','xvfb-run'}.issubset(ancestors), 'Use fresh D-Bus and Xvfb wrappers, not a desktop session.'
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='amoled-cinnamon-update-') as tmp:
 home=Path(tmp);(home/'.config/autostart').mkdir(parents=True)
 env={k:v for k,v in os.environ.items() if not k.startswith(('GH_','GITHUB_','ACTIONS_')) and 'TOKEN' not in k and 'SECRET' not in k}
 env.update(HOME=str(home),GSETTINGS_BACKEND='keyfile',XDG_CURRENT_DESKTOP='X-Cinnamon',XDG_SESSION_TYPE='x11',CLUTTER_BACKEND='x11',GDK_BACKEND='x11',LIBGL_ALWAYS_SOFTWARE='1');env.pop('GTK_THEME',None)
 for key,directory in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_RUNTIME_DIR','runtime')]:
  p=home/directory;p.mkdir(mode=0o700);env[key]=str(p)
 def run(*args):
  p=subprocess.run(args,env=env,capture_output=True,text=True,timeout=60);assert p.returncode==0,p.stdout+p.stderr;return p.stdout
 run('bash',str(root/'install.sh'),'--accent','blue','--activate')
 run('dbus-update-activation-environment','HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME','XDG_RUNTIME_DIR','GSETTINGS_BACKEND','DISPLAY','XAUTHORITY','XDG_CURRENT_DESKTOP','XDG_SESSION_TYPE')
 with (out/'session.log').open('w') as log:
  session=subprocess.Popen(['cinnamon-session','--session','cinnamon','--debug'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);app=None
  try:
   proxy=Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION,Gio.DBusProxyFlags.NONE,None,'org.Cinnamon','/org/Cinnamon','org.Cinnamon',None)
   def evaluate(js):
    ok,data=proxy.call_sync('Eval',GLib.Variant('(s)',(js,)),Gio.DBusCallFlags.NONE,10000,None).unpack();assert ok,data;return json.loads(data)
   for _ in range(900):
    assert session.poll() is None,'Cinnamon exited'
    try:
     if evaluate('imports.ui.main.runState === imports.ui.main.RunState.RUNNING'):break
    except GLib.Error:pass
    time.sleep(.1)
   else:raise AssertionError('Cinnamon not ready')
   app=subprocess.Popen(['python3','-c',"import gi;gi.require_version('Gtk','3.0');from gi.repository import Gtk;w=Gtk.Window(title='Accent update');w.set_default_size(500,300);w.show_all();Gtk.main()"],env=env,stdout=log,stderr=log)
   time.sleep(1)
   sample=r"""(() => {
    const St=imports.gi.St,c=St.ThemeContext.get_for_stage(global.stage),t=c.get_theme(),r=c.get_root_node();
    const node=(id,cls,state,parent=r,type=St.Widget.$gtype)=>St.ThemeNode.new(c,parent,t,type,id,cls,state,'',false);
    const result={};
    for(const id of ['menu-search-entry','appmenu-search-entry'])
      result[id]=node(id,null,'focus',r,St.Entry.$gtype).get_border_color(St.Side.TOP).to_string();
    const calendar=node(null,'calendar',null);
    result.calendar=node(null,'calendar-day-base calendar-day calendar-today',null,calendar).get_background_color().to_string();
    const panel=node('panel','panel-bottom',null);
    result.grouped=node(null,'grouped-window-list-item-box','active',panel).get_background_color().to_string();
    result.window=node(null,'window-list-item-box','active',panel).get_box_shadow().color.to_string();
    result.hover=node(null,'grouped-window-list-item-box','hover',panel).get_box_shadow().color.to_string();
    result.popup=node(null,'popup-menu-item','hover').get_background_color().to_string();
    result.theme=imports.ui.main.themeManager.themeDirectory;
    return result;
   })()"""
   sys.path.insert(0,str(root/'tools'));import generate_palette as palette
   records=[]
   def screenshot(name):
    time.sleep(.4)
    window=Gdk.get_default_root_window();pix=Gdk.pixbuf_get_from_window(window,0,0,window.get_width(),window.get_height())
    pix.savev(str(out/(name+'.png')),'png',[],[])
    return bytes(pix.get_pixels())
   def open_applet(uuid):
    data=evaluate("imports.ui.appletManager.definitions.filter(d=>d.applet).map(d=>{let a=d.applet.actor,p=a.get_transformed_position(),s=a.get_transformed_size();return {uuid:d.real_uuid||d.uuid,x:p[0],y:p[1],w:s[0],h:s[1]};})")
    target=next(a for a in data if a['uuid']==uuid and a['w']>0 and a['h']>0)
    run('xdotool','mousemove',str(round(target['x']+target['w']/2)),str(round(target['y']+target['h']/2)),'click','1')
   for index,color in enumerate(('blue','pink','green','yellow','gold','purple','red','orange','blue')):
    if index:
     # Alternate ordinary reinstalls and the new update-only entry point. Neither
     # changes the selected theme name; both must refresh the live shell CSS.
     options=('--recolor',) if index%2 else ('--activate',)
     output=run('bash',str(root/'install.sh'),'--accent',color,*options)
     assert 'Cinnamon desktop theme reloaded' in output,output
    colors=palette.preset_colors(root,color)
    expected={'menu-search-entry':colors['accent_text']+'ff','appmenu-search-entry':colors['accent_text']+'ff',
              'calendar':colors['accent_indicator']+'40','grouped':colors['accent_indicator']+'14',
              'window':colors['accent_text']+'ff','hover':colors['accent_text']+'ff','popup':colors['accent_fill']+'ff'}
    time.sleep(.4);actual=evaluate(sample)
    records.append({'accent':color,'expected':expected,'actual':actual})
    (out/'results.json').write_text(json.dumps(records,indent=2)+'\n')
    for name,value in expected.items():assert actual[name]==value,(color,name,actual[name],value)
    assert actual['theme'].endswith('/Adwaita-AMOLED/cinnamon'),actual
    open_applet('menu@cinnamon.org');pixels=screenshot(f'{index}-{color}-menu')
    # The real start menu must paint its pale accent, beyond synthetic nodes.
    assert pixels.count(bytes.fromhex(colors['accent_text'][1:]))>100,(color,'menu accent not painted')
    run('xdotool','key','Escape');time.sleep(.2)
    open_applet('calendar@cinnamon.org');screenshot(f'{index}-{color}-calendar')
    real_calendar=evaluate("(() => {let found=[];const walk=a=>{if(a.mapped&&a.get_style_class_name&&/(^| )calendar-today( |$)/.test(a.get_style_class_name()||''))found.push(a.get_theme_node().get_background_color().to_string());for(let ch of a.get_children())walk(ch);};walk(global.stage);return found;})()")
    assert expected['calendar'] in real_calendar,(color,'actual calendar',real_calendar)
    run('xdotool','key','Escape');time.sleep(.2)
    print(color,'live accent passed',flush=True)
   print(json.dumps({'transitions':len(records)-1,'color_states':len(records),'properties_per_state':7,'screenshots':len(records)*2}))
  finally:
   if app is not None:app.terminate();app.wait(timeout=10)
   try:os.killpg(session.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   try:session.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(session.pid,signal.SIGKILL);session.wait()
