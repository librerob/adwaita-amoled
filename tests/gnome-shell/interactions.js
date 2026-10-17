// Exercise real Shell actors and pointer events for reported interaction defects.
import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Shell from 'gi://Shell';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as Config from 'resource:///org/gnome/shell/misc/config.js';
import * as Scripting from 'resource:///org/gnome/shell/ui/scripting.js';
import {QuickMenuToggle} from 'resource:///org/gnome/shell/ui/quickSettings.js';

function assert(value, message) {
    if (!value)
        throw new Error(message);
}
function descendants(actor) {
    return [actor, ...actor.get_children().flatMap(descendants)];
}
function find(actor, cls) {
    return descendants(actor).filter(a => a.has_style_class_name?.(cls));
}
async function screenshot(name) {
    const stream = Gio.File.new_for_path(`${GLib.getenv('THEME_TEST_OUTPUT')}/interaction-${name}.png`)
        .replace(null, false, Gio.FileCreateFlags.REPLACE_DESTINATION, null);
    await new Shell.Screenshot().screenshot(false, stream);
    stream.close(null);
}
export async function checkInteractions() {
    const result = {version: Config.PACKAGE_VERSION, states: []};
    const backend = global.stage.context?.get_backend() ?? Clutter.get_default_backend();
    const seat = backend.get_default_seat();
    const pointer = seat.create_virtual_device(Clutter.InputDeviceType.POINTER_DEVICE);
    const hover = async actor => {
        const [x, y] = actor.get_transformed_position();
        const [w, h] = actor.get_transformed_size();
        assert(w > 0 && h > 0, 'Target has no visible allocation');
        pointer.notify_absolute_motion(GLib.get_monotonic_time(), x + w / 2, y + h / 2);
        await Scripting.sleep(180);
        // Mutter's test-monitor backend can constrain absolute virtual-device
        // X coordinates. Relative virtual motion still traverses the real seat.
        const [px, py] = global.get_pointer();
        if (px < x || px >= x + w || py < y || py >= y + h) {
            pointer.notify_relative_motion(GLib.get_monotonic_time(), x + w / 2 - px, y + h / 2 - py);
            await Scripting.sleep(180);
        }
    };
    const click = async actor => {
        await hover(actor);
        pointer.notify_button(GLib.get_monotonic_time(), 1, Clutter.ButtonState.PRESSED);
        await Scripting.sleep(50);
        pointer.notify_button(GLib.get_monotonic_time(), 1, Clutter.ButtonState.RELEASED);
        await Scripting.sleep(180);
    };
    const background = actor => actor.get_theme_node().get_background_color().to_string();
    Main.overview.hide();
    await Scripting.sleep(300);
    const clock = Main.panel.statusArea.dateMenu;
    // Upstream paints the clock label, excluding its notification indicator.
    const clockFace = find(clock, 'clock')[0];
    assert(clockFace, 'Panel clock face not found');
    const clockPaint = () => clockFace.get_theme_node().get_box_shadow()?.color.to_string() ?? background(clockFace);
    const panelNormal = clockPaint();
    await hover(clock);
    const panelHover = clockPaint();
    assert(panelHover !== panelNormal, `Panel clock hover has no feedback: ${panelNormal}/${panelHover}`);
    await click(clock);
    const dateMenu = clock.menu;
    assert(dateMenu.isOpen, 'Panel clock click did not open calendar');
    result.states.push({name: 'panel-clock', normal: panelNormal, hovered: panelHover});
    await Scripting.sleep(300);
    const days = find(dateMenu.box, 'calendar-day').filter(a => a.reactive && !a.has_style_class_name('calendar-today') && !a.has_style_class_name('calendar-other-month'));
    assert(days.length > 0, 'No real selectable calendar day found');
    const day = days[2] ?? days[0];
    const normal = background(day);
    await hover(day);
    const hovered = background(day);
    print(`AMOLED_INTERACTION calendar hover=${day.hover} pointer=${global.get_pointer()} classes=${day.get_style_class_name()} normal=${normal} hover=${hovered}`);
    await screenshot('calendar-hover');
    assert(normal !== hovered && !hovered.endsWith('00'), `Calendar hover has no visible background: ${normal}/${hovered}`);
    await click(day);
    const selected = background(day);
    assert(day.has_style_pseudo_class('active') || day.has_style_pseudo_class('selected') || selected !== normal, 'Clicked calendar day has no selection feedback');
    result.states.push({name: 'calendar', normal, hovered, selected});
    // GNOME 51 removed this calendar control. Test the actual 46 control,
    // rather than constructing a switch that the newer calendar does not use.
    if (Config.PACKAGE_VERSION.startsWith('46.')) {
        const switches = find(dateMenu.box, 'toggle-switch');
        assert(switches.length > 0, 'Do Not Disturb switch not found');
        const toggle = switches[0];
        const offImage = toggle.get_theme_node().get_background_image()?.get_path();
        assert(offImage && Gio.File.new_for_path(offImage).query_exists(null), `Missing GNOME 46 switch image: ${offImage}`);
        await screenshot('calendar-selected-switch-off');
        const dnd = find(dateMenu.box, 'dnd-button')[0] ?? toggle.get_parent();
        await click(dnd);
        await screenshot('calendar-switch-on');
        const onImage = toggle.get_theme_node().get_background_image()?.get_path();
        assert(onImage && onImage !== offImage && Gio.File.new_for_path(onImage).query_exists(null), `Switch image did not change: ${offImage}/${onImage}`);
        result.states.push({name: 'do-not-disturb', offImage, onImage});
        await click(dnd);
    }
    dateMenu.close();
    Main.overview.show();
    await Scripting.sleep(350);
    const showApps = Main.overview.dash.showAppsButton;
    const icon = find(showApps, 'overview-icon')[0];
    assert(icon, 'Real Show Apps icon actor not found');
    pointer.notify_absolute_motion(GLib.get_monotonic_time(), 20, 20);
    await Scripting.sleep(180);
    const dashNormal = background(icon);
    await hover(showApps);
    const dashHover = background(icon);
    assert(dashNormal !== dashHover && !dashHover.endsWith('00'), `Dash hover has no visible background: ${dashNormal}/${dashHover}`);
    result.states.push({name: 'dash', normal: dashNormal, hovered: dashHover});
    await screenshot('dash-hover');
    const app = descendants(Main.overview.dash).find(a =>
        a.has_style_class_name?.('overview-tile') || a.has_style_class_name?.('app-well-app'));
    assert(app, 'Favorite application tile not found');
    const appIcon = find(app, 'overview-icon')[0];
    assert(appIcon, 'Favorite application icon not found');
    const appNormal = background(appIcon);
    await hover(app);
    const appHover = background(appIcon);
    assert(appNormal !== appHover, `Application icon hover has no feedback: ${appNormal}/${appHover}`);
    result.states.push({name: 'dash-app', normal: appNormal, hovered: appHover});
    await screenshot('dash-app-hover');
    Main.overview.hide();
    await Scripting.sleep(300);
    const quick = Main.panel.statusArea.quickSettings.menu;
    quick.open();
    await Scripting.sleep(300);
    await screenshot('quick-settings');
    const splitClass = Config.PACKAGE_VERSION.startsWith('46.') ? 'quick-menu-toggle' : 'quick-toggle-has-menu';
    let containers = find(quick.box, splitClass);
    let fixture = null;
    if (!containers.some(a => a.visible && a.get_transformed_size()[0] > 0) && !Config.PACKAGE_VERSION.startsWith('46.')) {
        // Newer Shell uses a different power-profile service than the mock.
        // Exercise its actual QuickMenuToggle widget in the real menu instead.
        fixture = new QuickMenuToggle({title: 'Power Mode', subtitle: 'Balanced',
            icon_name: 'power-profile-balanced-symbolic', toggle_mode: true});
        quick.addItem(fixture);
        await Scripting.sleep(200);
        containers = find(quick.box, splitClass);
    }
    const split = containers.find(a => a.visible && a.get_transformed_size()[0] > 0);
    assert(split, 'No allocated quick-settings split button');
    const button = find(split, 'quick-toggle')[0];
    const arrow = find(split, Config.PACKAGE_VERSION.startsWith('46.') ? 'quick-toggle-arrow' : 'quick-toggle-menu-button')[0];
    assert(button && arrow, 'Split toggle children missing');
    const [bx] = button.get_transformed_position();
    const [bw] = button.get_transformed_size();
    const [ax] = arrow.get_transformed_position();
    assert(ax >= bx + bw - 2, `Menu arrow overlaps main button: ${bx}/${bw}/${ax}`);
    result.states.push({name: 'quick-settings-split', buttonWidth: bw, arrowX: ax, buttonX: bx, fixture: fixture !== null});
    await hover(button);
    await screenshot('quick-settings-hover');
    quick.close();
    fixture?.destroy();
    return result;
}
