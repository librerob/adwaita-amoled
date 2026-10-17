// Test-only extension used when distro Shell lacks --automation-script.
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

export default class InteractionTest extends Extension {
    enable() {
        this._timer = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 2000, () => {
            this._timer = 0;
            this._run();
            return GLib.SOURCE_REMOVE;
        });
    }
    async _run() {
        try {
            const uri = Gio.File.new_for_path(`${GLib.getenv('THEME_TEST_ROOT')}/tests/gnome-shell/interactions.js`).get_uri();
            const {checkInteractions} = await import(uri);
            const result = await checkInteractions();
            GLib.file_set_contents(`${GLib.getenv('THEME_TEST_OUTPUT')}/shell-interactions.json`, JSON.stringify(result, null, 2));
        } catch (error) {
            logError(error);
            GLib.file_set_contents(`${GLib.getenv('THEME_TEST_OUTPUT')}/shell-interactions.json`, JSON.stringify({error: String(error), stack: error.stack}));
        } finally {
            global.context.terminate();
        }
    }
    disable() {
        if (this._timer)
            GLib.source_remove(this._timer);
        this._timer = 0;
    }
}
