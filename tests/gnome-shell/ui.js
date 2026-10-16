// Native GNOME Shell 51 automation; run by session.sh on isolated test buses.
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';
import Shell from 'gi://Shell';
import * as Config from 'resource:///org/gnome/shell/misc/config.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as MessageTray from 'resource:///org/gnome/shell/ui/messageTray.js';
import * as ModalDialog from 'resource:///org/gnome/shell/ui/modalDialog.js';
import * as Scripting from 'resource:///org/gnome/shell/ui/scripting.js';

export const METRICS = {};
const results = {surfaces: {}, views: [], transitions: 0, styleNodes: 0};

export function init() {
    print('AMOLED_SHELL_PHASE automation-loaded');
}

function assert(condition, message) {
    if (!condition)
        throw new Error(message);
}

async function capture(name) {
    print(`AMOLED_SHELL_VIEW ${name}`);
    const directory = GLib.getenv('THEME_TEST_OUTPUT');
    if (directory) {
        const screenshot = new Shell.Screenshot();
        const stream = Gio.File.new_for_path(`${directory}/shell-${name}.png`)
            .replace(null, false, Gio.FileCreateFlags.REPLACE_DESTINATION, null);
        await screenshot.screenshot(false, stream);
        stream.close(null);
    }
    results.views.push(name);
}

export async function run() {
    assert(Config.PACKAGE_VERSION.startsWith('51.'), `Expected Shell 51, got ${Config.PACKAGE_VERSION}`);
    await Scripting.sleep(500);
    const stylesheet = Main.getThemeStylesheet();
    assert(stylesheet?.get_path()?.endsWith('/Adwaita-AMOLED/gnome-shell/gnome-shell.css'),
        `User Themes did not load Adwaita-AMOLED: ${stylesheet?.get_path()}`);
    const context = St.ThemeContext.get_for_stage(global.stage);
    print('AMOLED_SHELL_PHASE native-surfaces');
    const theme = context.get_theme();
    let root = context.get_root_node();
    const node = (id, cls, state = null, parent = root) =>
        St.ThemeNode.new(context, parent, theme, St.Widget.$gtype, id, cls, state, '');
    for (const [name, id, cls, expected] of [
        ['panel', 'panel', null, '#000000ff'],
        ['overview', 'overviewGroup', null, '#000000ff'],
        ['popover', null, 'popup-menu-content', '#000000ff'],
        ['dialog', null, 'modal-dialog', '#000000ff'],
        ['osd', null, 'osd-window', '#141414ff'],
    ]) {
        const style = node(id, cls);
        const background = style.get_background_color().to_string();
        const foreground = style.get_foreground_color().to_string();
        assert(background === expected, `${name}: expected ${expected}, got ${background}`);
        assert(foreground === '#ffffffff', `${name}: expected white text, got ${foreground}`);
        results.surfaces[name] = {background, foreground};
    }
    const dash = node('dash', null);
    assert(node(null, 'dash-background', null, dash).get_background_color().to_string() === '#0f0f0fff',
        'Dash surface must use the AMOLED raised surface');

    const [, bytes] = stylesheet.load_contents(null);
    const css = new TextDecoder().decode(bytes);
    const classes = [...new Set([...css.matchAll(/(?<![\w.])\.([a-zA-Z_][\w-]*)/g)].map(match => match[1]))];
    const states = ['', 'hover', 'active', 'checked', 'focus', 'insensitive', 'backdrop', 'rtl', 'checked:hover'];
    for (const scale of [1, 2]) {
        print(`AMOLED_SHELL_PHASE style-nodes-scale-${scale}`);
        context.set_scale_factor(scale);
        root = context.get_root_node();
        for (const cls of classes) {
            for (const state of states) {
                const style = node(null, cls, state);
                style.get_background_color();
                style.get_foreground_color();
                style.get_background_image();
                style.get_border_image();
                style.get_box_shadow();
                style.get_font();
                results.styleNodes++;
            }
        }
    }
    context.set_scale_factor(1);
    Main.overview.hide();
    await Scripting.sleep(300);
    await capture('desktop');
    Main.overview.show();
    await Scripting.sleep(300);
    assert(Main.overview.visible, 'Overview did not open');
    await capture('overview');
    Main.overview.dash.showAppsButton.checked = true;
    await Scripting.sleep(300);
    await capture('applications');
    Main.overview.dash.showAppsButton.checked = false;
    Main.overview.hide();
    await Scripting.sleep(300);

    for (const [name, menu] of [
        ['quick-settings', Main.panel.statusArea.quickSettings.menu],
        ['calendar', Main.panel.statusArea.dateMenu.menu],
    ]) {
        for (let iteration = 0; iteration < 10; iteration++) {
            menu.open();
            await Scripting.sleep(30);
            assert(menu.isOpen, `${name} did not open`);
            if (iteration === 0) {
                await Scripting.sleep(200);
                await capture(name);
            }
            menu.close();
            await Scripting.sleep(30);
            assert(!menu.isOpen, `${name} did not close`);
            results.transitions += 2;
        }
    }

    // Startup warnings can stay on screen without input in a headless session.
    // Dismiss them through the notification API before testing our own banner.
    for (const source of Main.messageTray.getSources()) {
        for (const notification of [...source.notifications])
            notification.destroy(MessageTray.NotificationDestroyedReason.DISMISSED);
    }
    await Scripting.sleep(300);
    Main.notify('AMOLED theme validation', 'A native notification with readable text.');
    for (let attempt = 0; attempt < 30; attempt++) {
        if (Main.messageTray._notification?.title === 'AMOLED theme validation' &&
            Main.messageTray._bannerBin.visible)
            break;
        await Scripting.sleep(100);
    }
    assert(Main.messageTray._notification?.title === 'AMOLED theme validation' &&
        Main.messageTray._bannerBin.visible, 'Theme test notification did not become visible');
    await capture('notification');
    Main.osdWindowManager.showAll(new Gio.ThemedIcon({name: 'audio-volume-high-symbolic'}),
        'Volume', 0.6, 1);
    await Scripting.sleep(200);
    assert(Main.osdWindowManager._osdWindows[0].visible, 'Volume OSD did not become visible');
    await capture('osd');
    const dialog = new ModalDialog.ModalDialog({destroyOnClose: false});
    dialog.contentLayout.add_child(new St.Label({text: 'Adwaita-AMOLED native dialog'}));
    dialog.setButtons([{label: 'Close', action: () => dialog.close()}]);
    assert(dialog.open(), 'Native modal dialog did not open');
    await Scripting.sleep(200);
    await capture('dialog');
    dialog.close();
    dialog.destroy();
    assert(results.views.length === 8, `Expected eight rendered views, got ${results.views.length}`);
    assert(results.transitions === 40 && results.styleNodes > 1000, 'Incomplete state coverage');
    results.version = Config.PACKAGE_VERSION;
    results.stylesheet = stylesheet.get_path();
    const output = GLib.getenv('THEME_TEST_OUTPUT');
    if (output)
        GLib.file_set_contents(`${output}/shell-results.json`, JSON.stringify(results, null, 2));
    print(`AMOLED_SHELL_RESULT ${JSON.stringify(results)}`);
}
