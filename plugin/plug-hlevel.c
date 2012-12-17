#ifndef NO_XLIB
#include "plug-internals.h"
#include "hlevel.h"
#include "xbasic.h"
#include <X11/Xlib.h>
struct p_win
{
  void * context;		/* application context for event callbacks */
  p_scr * s;

  Drawable d;
  p_win * parent;		/* non-0 only for offscreen pixmaps */
  int is_menu;		/* non-0 only for menus */

  Colormap cmap;
  p_col_t * pixels, *rgb_pixels;
  int n_palette;		/* number of pixels[] belonging to palette */
  int x, y, width, height, xyclip[4];
};

long GhXid(int number)
{
  Engine * display = ghDevices[number].display;
  XEngine * xeng = GisXEngine(display);

  if (!xeng || !xeng->win)
    { return -1; }

  return xeng->win->d;
}

void GhSetHint(int number, int value)
{
  Engine * display = ghDevices[number].display;
  XEngine * xeng = GisXEngine(display);

  if (!xeng || !xeng->win)
    { return; }

  /*
   * Display *dpy = w->s->xdpy->dpy;
   * if (!wm_hints) wm_hints = XAllocWMHints();
   * wm_hints = XGetWMHints(dpy,w->d);
   * wm_hints->input = value;
   * wm_hints->flags |= InputHint;
   * XSetWMHints(dpy, w->d, wm_hints);
   */
}
#else
long GhXid(int number)
{
  return -1;
}

void GhSetHint(int number, int value)
{
  return;
}
#endif
