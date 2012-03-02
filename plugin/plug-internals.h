#include "draw.h"

/*=== privately owned by yorick .c ===*/
typedef struct GfakeSystem GfakeSystem;
struct GfakeSystem {
  double viewport[4];    /* [xmin,xmax,ymin,ymax] in NDC coordinates */
  GaTickStyle ticks;     /* tick style for this coordinate system */
  char *legend;          /* e.g.- "System 0" or "System 1", p_malloc */
};
extern int raw_style(long nsys, int *landscape,
		     GfakeSystem *systems, GeLegendBox *legends);

/*=== end private ===*/
