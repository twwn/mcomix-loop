/* vptr X Y SECS: a virtual pointer in a wlroots compositor, put at X,Y of
   a 1920x1080 output and kept there, unmoved, for SECS seconds. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <wayland-client.h>
#include "vp.h"

static struct wl_seat *seat;
static struct zwlr_virtual_pointer_manager_v1 *manager;

static void global(void *data, struct wl_registry *registry, uint32_t name,
                   const char *interface, uint32_t version)
{
    if (strcmp(interface, "wl_seat") == 0)
        seat = wl_registry_bind(registry, name, &wl_seat_interface, 1);
    else if (strcmp(interface, zwlr_virtual_pointer_manager_v1_interface.name) == 0)
        manager = wl_registry_bind(registry, name,
                                   &zwlr_virtual_pointer_manager_v1_interface, 1);
}

static void global_remove(void *data, struct wl_registry *registry, uint32_t name) {}

static const struct wl_registry_listener listener = { global, global_remove };

int main(int argc, char **argv)
{
    if (argc != 4) return 2;
    struct wl_display *display = wl_display_connect(NULL);
    if (!display) { fprintf(stderr, "vptr: no display\n"); return 1; }
    struct wl_registry *registry = wl_display_get_registry(display);
    wl_registry_add_listener(registry, &listener, NULL);
    wl_display_roundtrip(display);
    if (!manager) { fprintf(stderr, "vptr: no virtual pointer manager\n"); return 1; }
    struct zwlr_virtual_pointer_v1 *pointer =
        zwlr_virtual_pointer_manager_v1_create_virtual_pointer(manager, seat);
    zwlr_virtual_pointer_v1_motion_absolute(pointer, 0, atoi(argv[1]), atoi(argv[2]), 1920, 1080);
    zwlr_virtual_pointer_v1_frame(pointer);
    wl_display_roundtrip(display);
    fprintf(stderr, "vptr: at %s,%s\n", argv[1], argv[2]);
    sleep(atoi(argv[3]));
    return 0;
}
