// Native GNOME Shell 51 automation; run by session.sh on isolated test buses.
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';
import MetaTest from 'gi://MetaTest';
import Shell from 'gi://Shell';
import * as Config from 'resource:///org/gnome/shell/misc/config.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as MessageTray from 'resource:///org/gnome/shell/ui/messageTray.js';
import * as ModalDialog from 'resource:///org/gnome/shell/ui/modalDialog.js';
import * as Scripting from 'resource:///org/gnome/shell/ui/scripting.js';

export const METRICS = {};
const results = {surfaces: {}, views: [], transitions: 0, styleNodes: 0};

let testMonitor = null;
export function init() {
    print('AMOLED_SHELL_PHASE automation-loaded');
    // Follow upstream tests/shell/headlessStart.js: connect the test monitor
    // after automation initialization, so startup-complete cannot be missed.
    global.connect('shutdown', () => testMonitor?.destroy());
    GLib.timeout_add(GLib.PRIORITY_DEFAULT, 200, () => {
        testMonitor = MetaTest.TestMonitor.new(global.context, 1600, 1200, 60.0);
        return GLib.SOURCE_REMOVE;
    });
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


function contrast(foreground, background) {
    const channels = color => [1, 3, 5].map(i => parseInt(color.slice(i, i + 2), 16) / 255);
    const luminance = color => channels(color).reduce((sum, value, i) => sum +
        (value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4) *
        [0.2126, 0.7152, 0.0722][i], 0);
    const [high, low] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
    return (high + 0.05) / (low + 0.05);
}

function composite(foreground, background) {
    const alpha = parseInt(foreground.slice(7, 9), 16) / 255;
    return '#' + [1, 3, 5].map(i => Math.round(parseInt(foreground.slice(i, i + 2), 16) * alpha +
        parseInt(background.slice(i, i + 2), 16) * (1 - alpha)).toString(16).padStart(2, '0')).join('') + 'ff';
}

async function checkAccentRoles(context, theme) {
    const settings = new Gio.Settings({schema_id: 'org.gnome.desktop.interface'});
    const original = settings.get_string('accent-color');
    const pairs = [];
    const graphics = [];
    const states = ['', 'hover', 'focus', 'active', 'active:hover', 'focus:hover', 'active:focus', 'active:focus:hover'];
    const make = (parent, classes, state = '', type = St.Widget.$gtype, id = null) =>
        St.ThemeNode.new(context, parent, theme, type, id, classes, state.replaceAll(':', ' '), '');
    try {
        for (const accent of ['blue', 'teal', 'green', 'yellow', 'orange', 'red', 'pink', 'purple', 'slate']) {
            settings.set_string('accent-color', accent);
            await Scripting.sleep(60);
            for (const [name, parentClass, childClass, baseState] of [
                ['default', null, 'button default', ''],
                ['quick-toggle', null, 'quick-toggle', 'checked'],
                ['calendar-today', 'calendar', 'calendar-day calendar-today', ''],
                ['quick-menu', 'quick-toggle-has-menu', 'quick-toggle-menu-button', 'checked'],
                ['input-candidate', null, 'candidate-box', 'selected'],
                ['monitor-label', null, 'osd-monitor-label', ''],
                ['keyboard-latched', null, 'keyboard-key default-key', 'latched'],
                ['emoji-latched', 'emoji-panel', 'keyboard-key', 'latched'],
                ['checkbox', null, '', 'checked'],
                ['switch-handle', null, '', 'checked'],
                ['debug-switch-handle', null, '', 'checked'],
                ['week-number', 'calendar', 'calendar-week-number', ''],
                ['word-suggestion', null, '', ''],
            ]) {
                for (const state of states) {
                    let parent = context.get_root_node();
                    if (parentClass)
                        parent = make(parent, parentClass);
                    const pseudo = [baseState, state].filter(Boolean).join(':');
                    let node, foreground, background;
                    if (name === 'checkbox') {
                        parent = make(parent, 'check-box', pseudo);
                        node = make(parent, null, '', St.Icon.$gtype);
                    } else if (name === 'switch-handle' || name === 'debug-switch-handle') {
                        if (name === 'debug-switch-handle') {
                            parent = make(parent, null, '', St.Widget.$gtype, 'LookingGlassDebugFlags');
                            parent = make(parent, 'lg-debug-flag-button');
                        }
                        parent = make(parent, 'toggle-switch', pseudo);
                        node = make(parent, 'handle');
                        foreground = node.get_background_color().to_string();
                        background = parent.get_background_color().to_string();
                    } else if (name === 'word-suggestion') {
                        parent = make(parent, null, '', St.BoxLayout.$gtype, 'keyboard');
                        const base = composite(parent.get_background_color().to_string(), '#000000ff');
                        parent = make(parent, 'word-suggestions');
                        node = make(parent, null, pseudo, St.Button.$gtype);
                        background = composite(node.get_background_color().to_string(), base);
                    } else if (name === 'week-number') {
                        const base = composite(parent.get_background_color().to_string(), '#000000ff');
                        node = make(parent, childClass, pseudo);
                        background = composite(node.get_background_color().to_string(), base);
                    } else {
                        node = make(parent, childClass, pseudo);
                    }
                    foreground ??= node.get_foreground_color().to_string();
                    background ??= node.get_background_color().to_string();
                    assert(background.endsWith('ff'), `${name} needs an opaque control background: ${background}`);
                    pairs.push({accent, name, state, foreground, background,
                        contrast: contrast(composite(foreground, background), background)});
                }
            }
            const bar = make(context.get_root_node(), null, '', St.ScrollBar.$gtype);
            for (const orientation of ['vhandle', 'hhandle']) {
                for (const state of ['', 'hover', 'active']) {
                    const handle = make(bar, orientation, state, St.Button.$gtype);
                    const foreground = handle.get_background_color().to_string();
                    for (const background of ['#000000ff', '#141414ff', '#1a1a1aff']) {
                        graphics.push({accent, orientation, state, foreground, background,
                            contrast: contrast(composite(foreground, background), background)});
                    }
                }
            }
        }
    } finally {
        settings.set_string('accent-color', original);
        await Scripting.sleep(60);
    }
    const output = GLib.getenv('THEME_TEST_OUTPUT');
    if (output) {
        GLib.file_set_contents(`${output}/shell-accent-colors.json`, JSON.stringify(pairs, null, 2));
        GLib.file_set_contents(`${output}/shell-graphic-colors.json`, JSON.stringify(graphics, null, 2));
    }
    const failures = pairs.filter(pair => pair.contrast < 4.5);
    assert(failures.length === 0, `Unreadable Shell control states: ${JSON.stringify(failures)}`);
    const graphicFailures = graphics.filter(pair => pair.contrast < 3);
    assert(graphicFailures.length === 0, `Unreadable Shell scrollbar states: ${JSON.stringify(graphicFailures)}`);
    results.accentPairs = pairs.length;
    results.minimumAccentContrast = Math.min(...pairs.map(pair => pair.contrast));
    results.graphicPairs = graphics.length;
    results.minimumGraphicContrast = Math.min(...graphics.map(pair => pair.contrast));
}

async function checkPlaceholderFonts(context, theme) {
    const original = context.get_font().copy();
    const pairs = [];
    try {
        for (const points of [9, 11, 14]) {
            const description = original.copy();
            description.set_size(points * 1024);
            context.set_font(description);
            await Scripting.sleep(60);
            const parent = St.ThemeNode.new(context, context.get_root_node(), theme, St.Widget.$gtype,
                null, 'message-list', null, '');
            const placeholder = St.ThemeNode.new(context, parent, theme, St.Widget.$gtype,
                null, 'message-list-placeholder', null, '');
            const label = St.ThemeNode.new(context, placeholder, theme, St.Label.$gtype,
                null, null, null, '');
            const foreground = label.get_foreground_color().to_string();
            const background = '#000000ff';
            pairs.push({points, font: label.get_font().to_string(), foreground, background,
                contrast: contrast(composite(foreground, background), background)});
        }
    } finally {
        context.set_font(original);
        await Scripting.sleep(60);
    }
    const output = GLib.getenv('THEME_TEST_OUTPUT');
    if (output)
        GLib.file_set_contents(`${output}/shell-font-colors.json`, JSON.stringify(pairs, null, 2));
    assert(pairs.every(pair => pair.contrast >= 4.5), `Unreadable Shell placeholder: ${JSON.stringify(pairs)}`);
    results.fontPairs = pairs.length;
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
        St.ThemeNode.new(context, parent, theme, St.Widget.$gtype, id, cls, state === null ? null : state.replaceAll(':', ' '), '');
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

    await checkAccentRoles(context, theme);
    await checkPlaceholderFonts(context, theme);

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
