/* A real Flatpak GTK/libadwaita consumer, independent of test-added CSS providers. */
#include <adwaita.h>
#include <cairo.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    adw_init();
    gboolean light = argc > 1 && strcmp(argv[1], "--light") == 0;
    adw_style_manager_set_color_scheme(adw_style_manager_get_default(),
        light ? ADW_COLOR_SCHEME_FORCE_LIGHT : ADW_COLOR_SCHEME_FORCE_DARK);
    GtkWidget *window = adw_window_new();
    GtkWidget *label = gtk_label_new("Accent text");
    gtk_widget_add_css_class(label, "accent");
    adw_window_set_content(ADW_WINDOW(window), label);
    gtk_window_set_default_size(GTK_WINDOW(window), 320, 160);
    gtk_window_present(GTK_WINDOW(window));
    gint64 deadline = g_get_monotonic_time() + 250000;
    while (g_get_monotonic_time() < deadline) {
        while (g_main_context_pending(NULL)) g_main_context_iteration(NULL, FALSE);
        g_usleep(2000);
    }
    GdkRGBA color;
    gtk_style_context_get_color(gtk_widget_get_style_context(label), &color);
    cairo_surface_t *surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 64, 64);
    cairo_t *cr = cairo_create(surface);
    cairo_set_source_rgb(cr, 1, 0, 1); cairo_paint(cr);
    gtk_render_background(gtk_widget_get_style_context(window), cr, 0, 0, 64, 64);
    cairo_surface_flush(surface);
    unsigned char *pixel = cairo_image_surface_get_data(surface) + 32*cairo_image_surface_get_stride(surface) + 32*4;
    printf("{\"gtk\":[%u,%u,%u],\"accent\":[%.0f,%.0f,%.0f],\"background\":[%u,%u,%u]}\n",
        gtk_get_major_version(), gtk_get_minor_version(), gtk_get_micro_version(),
        color.red*255, color.green*255, color.blue*255, pixel[2], pixel[1], pixel[0]);
    cairo_destroy(cr); cairo_surface_destroy(surface);
    gtk_window_destroy(GTK_WINDOW(window));
    return 0;
}
