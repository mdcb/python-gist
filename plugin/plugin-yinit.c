/* codger-generated yorick initialization file */
#include "play.h"
#include "ydata.h"

static char *yhome = "/opt/yorick/Linux-i686";
static char *ysite = "/opt/yorick";

extern y_pkg_t yk_yor;

static y_pkg_t *ypkgs[] = {
  &yk_yor,
  0
};

int
on_launch(int argc, char *argv[])
{
  return y_launch(argc, argv, yhome, ysite, ypkgs);
}
