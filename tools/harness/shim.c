// LD_PRELOAD shim for headless, scripted testing of Augustus.
//
// Intercepts SDL_PollEvent to inject scripted input and SDL_RenderPresent to
// capture screenshots. Script file (env AUG_SCRIPT) lines:
//   <ms> move X Y
//   <ms> click X Y          (left click)
//   <ms> rclick X Y         (right click)
//   <ms> key SCANCODE SYM   (press + release)
//   <ms> text STRING        (SDL_TEXTINPUT)
//   <ms> shot NAME          (writes $AUG_SHOTDIR/NAME.ppm on next present)
//   <ms> quit
// Times are milliseconds since the first SDL_PollEvent call.
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef union {
    uint32_t type;
    uint8_t padding[56];
} SDL_Event;

typedef struct {
    uint32_t type, timestamp, windowID;
    uint8_t state, repeat, p2, p3;
    int32_t scancode, sym;
    uint16_t mod;
    uint32_t unused;
} KeyEv;

typedef struct {
    uint32_t type, timestamp, windowID, which;
    uint8_t button, state, clicks, p1;
    int32_t x, y;
} ButtonEv;

typedef struct {
    uint32_t type, timestamp, windowID, which, state;
    int32_t x, y, xrel, yrel;
} MotionEv;

typedef struct {
    uint32_t type, timestamp, windowID;
    char text[32];
} TextEv;

enum { EV_MOVE, EV_CLICK, EV_RCLICK, EV_KEY, EV_TEXT, EV_SHOT, EV_QUIT, EV_DRAG };

typedef struct {
    uint32_t ms;
    int kind;
    int a, b, c, d;
    char str[64];
} script_ev;

static script_ev evs[4096];
static int num_evs, next_ev, loaded;
static uint32_t start_ms;
static SDL_Event queue[64];
static int q_head, q_tail;
static char pending_shot[64];
static int mouse_x, mouse_y;

static uint32_t (*real_GetTicks)(void);
static int parse_line(char *line, uint32_t now);

static void load_script(void)
{
    loaded = 1;
    real_GetTicks = dlsym(RTLD_DEFAULT, "SDL_GetTicks");
    start_ms = real_GetTicks();
    const char *path = getenv("AUG_SCRIPT");
    if (!path) {
        return;
    }
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return;
    }
    char line[256];
    while (fgets(line, sizeof(line), fp) && num_evs < 4096) {
        parse_line(line, 0);
    }
    fclose(fp);
}

static int parse_line(char *line, uint32_t now)
{
    {
        script_ev *e = &evs[num_evs];
        char cmd[32];
        memset(e, 0, sizeof(*e));
        if (now) {
            if (sscanf(line, "%31s", cmd) != 1) {
                return 0;
            }
            e->ms = now;
        } else if (sscanf(line, "%u %31s", &e->ms, cmd) != 2) {
            return 0;
        }
        char *rest = strstr(line, cmd) + strlen(cmd);
        if (!strcmp(cmd, "move")) { e->kind = EV_MOVE; sscanf(rest, "%d %d", &e->a, &e->b); }
        else if (!strcmp(cmd, "click")) { e->kind = EV_CLICK; sscanf(rest, "%d %d", &e->a, &e->b); }
        else if (!strcmp(cmd, "rclick")) { e->kind = EV_RCLICK; sscanf(rest, "%d %d", &e->a, &e->b); }
        else if (!strcmp(cmd, "key")) { e->kind = EV_KEY; sscanf(rest, "%d %d", &e->a, &e->b); }
        else if (!strcmp(cmd, "text")) { e->kind = EV_TEXT; sscanf(rest, " %63[^\n]", e->str); }
        else if (!strcmp(cmd, "shot")) { e->kind = EV_SHOT; sscanf(rest, " %63s", e->str); }
        else if (!strcmp(cmd, "quit")) { e->kind = EV_QUIT; }
        else if (!strcmp(cmd, "drag")) { e->kind = EV_DRAG; sscanf(rest, "%d %d %d %d", &e->a, &e->b, &e->c, &e->d); }
        else return 0;
        num_evs++;
    }
    return 1;
}

/* live mode: lines appended to $AUG_CMDFILE are executed immediately */
static long cmd_offset;
static void poll_cmdfile(void)
{
    const char *path = getenv("AUG_CMDFILE");
    if (!path || num_evs >= 4000) {
        return;
    }
    FILE *fp = fopen(path, "r");
    if (!fp) {
        return;
    }
    fseek(fp, cmd_offset, SEEK_SET);
    char line[256];
    uint32_t now = real_GetTicks() - start_ms;
    while (fgets(line, sizeof(line), fp)) {
        if (!strchr(line, '\n')) {
            break; /* incomplete line, read again later */
        }
        cmd_offset = ftell(fp);
        parse_line(line, now ? now : 1);
    }
    fclose(fp);
}

static void push(SDL_Event *e)
{
    queue[q_tail] = *e;
    q_tail = (q_tail + 1) % 64;
}

static void motion(int x, int y)
{
    SDL_Event e;
    memset(&e, 0, sizeof(e));
    MotionEv *m = (MotionEv *) &e;
    m->type = 0x400;
    m->windowID = 1;
    m->x = x; m->y = y; m->xrel = x - mouse_x; m->yrel = y - mouse_y;
    mouse_x = x; mouse_y = y;
    push(&e);
}

static void button(int x, int y, int btn, int down)
{
    SDL_Event e;
    memset(&e, 0, sizeof(e));
    ButtonEv *b = (ButtonEv *) &e;
    b->type = down ? 0x401 : 0x402;
    b->windowID = 1;
    b->button = btn; b->state = down; b->clicks = 1;
    b->x = x; b->y = y;
    push(&e);
}

static void key(int scancode, int sym, int down)
{
    SDL_Event e;
    memset(&e, 0, sizeof(e));
    KeyEv *k = (KeyEv *) &e;
    k->type = down ? 0x300 : 0x301;
    k->windowID = 1;
    k->state = down;
    k->scancode = scancode; k->sym = sym;
    push(&e);
}

static void schedule(void)
{
    static uint32_t last_poll;
    uint32_t now = real_GetTicks() - start_ms;
    if (now - last_poll > 100) {
        last_poll = now;
        poll_cmdfile();
    }
    // only release one script event per poll cycle so the game sees discrete frames
    if (next_ev < num_evs && evs[next_ev].ms <= now && q_head == q_tail) {
        script_ev *s = &evs[next_ev++];
        SDL_Event e;
        switch (s->kind) {
            case EV_MOVE: motion(s->a, s->b); break;
            case EV_CLICK: motion(s->a, s->b); button(s->a, s->b, 1, 1); button(s->a, s->b, 1, 0); break;
            case EV_RCLICK: motion(s->a, s->b); button(s->a, s->b, 3, 1); button(s->a, s->b, 3, 0); break;
            case EV_DRAG:
                motion(s->a, s->b);
                button(s->a, s->b, 1, 1);
                for (int i = 1; i <= 20; i++) {
                    motion(s->a + (s->c - s->a) * i / 20, s->b + (s->d - s->b) * i / 20);
                }
                button(s->c, s->d, 1, 0);
                break;
            case EV_KEY: key(s->a, s->b, 1); key(s->a, s->b, 0); break;
            case EV_TEXT:
                memset(&e, 0, sizeof(e));
                ((TextEv *) &e)->type = 0x303;
                ((TextEv *) &e)->windowID = 1;
                strncpy(((TextEv *) &e)->text, s->str, 31);
                push(&e);
                break;
            case EV_SHOT: strncpy(pending_shot, s->str, 63); break;
            case EV_QUIT:
                memset(&e, 0, sizeof(e));
                e.type = 0x100;
                push(&e);
                break;
        }
    }
}

int SDL_PollEvent(SDL_Event *event)
{
    static int (*real)(SDL_Event *);
    if (!real) {
        real = dlsym(RTLD_NEXT, "SDL_PollEvent");
    }
    if (!loaded) {
        load_script();
    }
    schedule();
    static int just_injected;
    if (just_injected) {
        // let the game finish this frame before the next injected event
        just_injected = 0;
        return real(event);
    }
    if (q_head != q_tail) {
        just_injected = 1;
        if (event) {
            *event = queue[q_head];
            q_head = (q_head + 1) % 64;
        }
        return 1;
    }
    return real(event);
}

uint32_t SDL_GetMouseState(int *x, int *y)
{
    if (x) *x = mouse_x;
    if (y) *y = mouse_y;
    return 0;
}

void SDL_RenderPresent(void *renderer)
{
    static void (*real)(void *);
    static int (*read_pixels)(void *, const void *, uint32_t, void *, int);
    static int (*output_size)(void *, int *, int *);
    if (!real) {
        real = dlsym(RTLD_NEXT, "SDL_RenderPresent");
        read_pixels = dlsym(RTLD_DEFAULT, "SDL_RenderReadPixels");
        output_size = dlsym(RTLD_DEFAULT, "SDL_GetRendererOutputSize");
    }
    if (pending_shot[0]) {
        int w = 0, h = 0;
        output_size(renderer, &w, &h);
        unsigned char *px = malloc((size_t) w * h * 4);
        // SDL_PIXELFORMAT_ABGR8888 == bytes R,G,B,A in memory on little endian
        if (px && read_pixels(renderer, 0, 0x16762004u, px, w * 4) == 0) {
            char path[512];
            const char *dir = getenv("AUG_SHOTDIR");
            snprintf(path, sizeof(path), "%s/%s.ppm", dir ? dir : ".", pending_shot);
            FILE *fp = fopen(path, "wb");
            if (fp) {
                fprintf(fp, "P6\n%d %d\n255\n", w, h);
                for (int i = 0; i < w * h; i++) {
                    fwrite(&px[i * 4], 1, 3, fp);
                }
                fclose(fp);
            }
        }
        free(px);
        pending_shot[0] = 0;
    }
    real(renderer);
}
