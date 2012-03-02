/* codger-generated yorick package wrapper file */
#include "play.h"
#include "ydata.h"

/*----------------begin std.i */
extern BuiltIn Y_help;
extern BuiltIn Y_quit;
extern BuiltIn Y_system;
extern BuiltIn Y_yorick_init;
extern BuiltIn Y_set_path;
extern BuiltIn Y_get_path;
extern BuiltIn Y_get_pkgnames;
extern BuiltIn Y_set_site;
extern BuiltIn Y_yorick_stats;
extern BuiltIn Y_disassemble;
extern BuiltIn Y_reshape;
extern BuiltIn Y_eq_nocopy;
extern BuiltIn Y_array;
extern BuiltIn Y_structof;
extern BuiltIn Y_dimsof;
extern BuiltIn Y_orgsof;
extern BuiltIn Y_use_origins;
extern BuiltIn Y_sizeof;
extern BuiltIn Y_numberof;
extern BuiltIn Y_typeof;
extern BuiltIn Y_nameof;
extern BuiltIn Y_print;
extern BuiltIn Y_print_format;
extern BuiltIn Y_is_array;
extern BuiltIn Y_is_func;
extern BuiltIn Y_is_void;
extern BuiltIn Y_is_range;
extern BuiltIn Y_is_struct;
extern BuiltIn Y_is_stream;
extern BuiltIn Y_is_list;
extern BuiltIn Y_am_subroutine;
extern BuiltIn Y_sin;
extern BuiltIn Y_cos;
extern BuiltIn Y_tan;
extern BuiltIn Y_asin;
extern BuiltIn Y_acos;
extern BuiltIn Y_atan;
extern BuiltIn Y_sinh;
extern BuiltIn Y_cosh;
extern BuiltIn Y_tanh;
extern BuiltIn Y_exp;
extern BuiltIn Y_log;
extern BuiltIn Y_log10;
extern BuiltIn Y_sqrt;
extern BuiltIn Y_poly;
extern BuiltIn Y_ceil;
extern BuiltIn Y_floor;
extern BuiltIn Y_abs;
extern BuiltIn Y_sign;
extern BuiltIn Y_conj;
extern BuiltIn Y_random;
extern BuiltIn Y_random_seed;
extern BuiltIn Y_min;
extern BuiltIn Y_max;
extern BuiltIn Y_sum;
extern BuiltIn Y_avg;
extern BuiltIn Y_allof;
extern BuiltIn Y_anyof;
extern BuiltIn Y_noneof;
extern BuiltIn Y_nallof;
extern BuiltIn Y_where;
extern BuiltIn Y_merge;
extern BuiltIn Y_grow;
extern BuiltIn Y__;
extern BuiltIn Y_indgen;
extern BuiltIn Y_span;
extern BuiltIn Y_digitize;
extern BuiltIn Y_histogram;
extern BuiltIn Y_interp;
extern BuiltIn Y_integ;
extern BuiltIn Y_sort;
extern BuiltIn Y_transpose;
extern BuiltIn Y_strlen;
extern BuiltIn Y_strchar;
extern BuiltIn Y_strpart;
extern BuiltIn Y_strcase;
extern BuiltIn Y_strword;
extern BuiltIn Y__strtok;
extern BuiltIn Y_strglob;
extern BuiltIn Y_strfind;
extern BuiltIn Y_strgrep;
extern BuiltIn Y_streplace;
extern BuiltIn Y_open;
extern BuiltIn Y_popen;
extern BuiltIn Y_fflush;
extern BuiltIn Y_close;
extern BuiltIn Y_rename;
extern BuiltIn Y_remove;
extern BuiltIn Y_read;
extern BuiltIn Y_sread;
extern BuiltIn Y_rdline;
extern BuiltIn Y_write;
extern BuiltIn Y_swrite;
extern BuiltIn Y_bookmark;
extern BuiltIn Y_backup;
extern BuiltIn Y_include;
extern BuiltIn Y_require;
extern BuiltIn Y_plug_in;
extern BuiltIn Y_plug_dir;
extern BuiltIn Y_autoload;
extern BuiltIn Y_cd;
extern BuiltIn Y_lsdir;
extern BuiltIn Y_mkdir;
extern BuiltIn Y_rmdir;
extern BuiltIn Y_get_cwd;
extern BuiltIn Y_get_home;
extern BuiltIn Y_get_env;
extern BuiltIn Y_get_argv;
extern BuiltIn Y_get_member;
extern BuiltIn Y_read_clog;
extern BuiltIn Y__not_pdb;
extern BuiltIn Y__init_pdb;
extern BuiltIn Y__set_pdb;
extern BuiltIn Y__init_clog;
extern BuiltIn Y_dump_clog;
extern BuiltIn Y_get_primitives;
extern BuiltIn Y_save;
extern BuiltIn Y_restore;
extern BuiltIn Y__jr;
extern BuiltIn Y__jt;
extern BuiltIn Y__jc;
extern BuiltIn Y_add_record;
extern BuiltIn Y_add_variable;
extern BuiltIn Y_set_blocksize;
extern BuiltIn Y_set_filesize;
extern BuiltIn Y_get_vars;
extern BuiltIn Y_set_vars;
extern BuiltIn Y_get_addrs;
extern BuiltIn Y_get_times;
extern BuiltIn Y_get_ncycs;
extern BuiltIn Y_edit_times;
extern BuiltIn Y__read;
extern BuiltIn Y__write;
extern BuiltIn Y_add_member;
extern BuiltIn Y_install_struct;
extern BuiltIn Y_data_align;
extern BuiltIn Y_struct_align;
extern BuiltIn Y_add_next_file;
extern BuiltIn Y_error;
extern BuiltIn Y_exit;
extern BuiltIn Y_catch;
extern BuiltIn Y_batch;
extern BuiltIn Y_set_idler;
extern BuiltIn Y_maybe_prompt;
extern BuiltIn Y_funcdef;
extern BuiltIn Y_spawn;
extern BuiltIn Y_suspend;
extern BuiltIn Y_resume;
extern BuiltIn Y_after;
extern BuiltIn Y_timestamp;
extern BuiltIn Y_timer;
extern BuiltIn Y_symbol_def;
extern BuiltIn Y_symbol_set;
extern BuiltIn Y_dbexit;
extern BuiltIn Y_dbcont;
extern BuiltIn Y_dbret;
extern BuiltIn Y_dbskip;
extern BuiltIn Y_dbup;
extern BuiltIn Y_dbinfo;
extern BuiltIn Y_dbdis;
extern BuiltIn Y_dbauto;
extern BuiltIn Y__lst;
extern BuiltIn Y__cat;
extern BuiltIn Y__car;
extern BuiltIn Y__cdr;
extern BuiltIn Y__cpy;
extern BuiltIn Y__len;

/*----------------begin matrix.i */
extern BuiltIn Y__dgtsv;

extern void dgtsv(long , long , double *, double *, double *, 
  double *, long , long *);
void
Y__dgtsv(int n)
{
  if (n!=8) YError("_dgtsv takes exactly 8 arguments");
  dgtsv(yarg_sl(7), yarg_sl(6), yarg_d(5,0), yarg_d(4,0), yarg_d(3,0), 
    yarg_d(2,0), yarg_sl(1), yarg_l(0,0));
}

extern BuiltIn Y__dgesv;

extern void dgesv(long , long , double *, long , long *, double *, 
  long , long *);
void
Y__dgesv(int n)
{
  if (n!=8) YError("_dgesv takes exactly 8 arguments");
  dgesv(yarg_sl(7), yarg_sl(6), yarg_d(5,0), yarg_sl(4), yarg_l(3,0), 
    yarg_d(2,0), yarg_sl(1), yarg_l(0,0));
}

extern BuiltIn Y__dgetrf;

extern void dgetrf(long , long , double *, long , long *, long *);
void
Y__dgetrf(int n)
{
  if (n!=6) YError("_dgetrf takes exactly 6 arguments");
  dgetrf(yarg_sl(5), yarg_sl(4), yarg_d(3,0), yarg_sl(2), 
    yarg_l(1,0), yarg_l(0,0));
}

extern BuiltIn Y__dgecox;

extern void dgecox(long , long , double *, long , double , double *, 
  double *, long *, long *);
void
Y__dgecox(int n)
{
  if (n!=9) YError("_dgecox takes exactly 9 arguments");
  dgecox(yarg_sl(8), yarg_sl(7), yarg_d(6,0), yarg_sl(5), 
    yarg_sd(4), yarg_d(3,0), yarg_d(2,0), yarg_l(1,0), yarg_l(0,0));
}

extern BuiltIn Y__dgelx;

extern void dgelx(long , long , long , long , double *, long , 
  double *, long , double *, long , long *);
void
Y__dgelx(int n)
{
  if (n!=11) YError("_dgelx takes exactly 11 arguments");
  dgelx(yarg_sl(10), yarg_sl(9), yarg_sl(8), yarg_sl(7), 
    yarg_d(6,0), yarg_sl(5), yarg_d(4,0), yarg_sl(3), yarg_d(2,0), 
    yarg_sl(1), yarg_l(0,0));
}

extern BuiltIn Y__dgelss;

extern void dgelss(long , long , long , double *, long , double *, 
  long , double *, double , long *, double *, long , long *);
void
Y__dgelss(int n)
{
  if (n!=13) YError("_dgelss takes exactly 13 arguments");
  dgelss(yarg_sl(12), yarg_sl(11), yarg_sl(10), yarg_d(9,0), 
    yarg_sl(8), yarg_d(7,0), yarg_sl(6), yarg_d(5,0), yarg_sd(4), 
    yarg_l(3,0), yarg_d(2,0), yarg_sl(1), yarg_l(0,0));
}

extern BuiltIn Y__dgesvx;

extern void dgesvx(long , long , long , double *, long , double *, 
  double *, long , double *, long , double *, long , long *);
void
Y__dgesvx(int n)
{
  if (n!=13) YError("_dgesvx takes exactly 13 arguments");
  dgesvx(yarg_sl(12), yarg_sl(11), yarg_sl(10), yarg_d(9,0), 
    yarg_sl(8), yarg_d(7,0), yarg_d(6,0), yarg_sl(5), yarg_d(4,0), 
    yarg_sl(3), yarg_d(2,0), yarg_sl(1), yarg_l(0,0));
}


/*----------------begin fft.i */
extern BuiltIn Y_fft_init;

extern void cffti(long , double *);
void
Y_fft_init(int n)
{
  if (n!=2) YError("fft_init takes exactly 2 arguments");
  cffti(yarg_sl(1), yarg_d(0,0));
}

extern BuiltIn Y_fft_fraw;

extern void cfftf(long , double *, double *);
void
Y_fft_fraw(int n)
{
  if (n!=3) YError("fft_fraw takes exactly 3 arguments");
  cfftf(yarg_sl(2), yarg_z(1,0), yarg_d(0,0));
}

extern BuiltIn Y_fft_braw;

extern void cfftb(long , double *, double *);
void
Y_fft_braw(int n)
{
  if (n!=3) YError("fft_braw takes exactly 3 arguments");
  cfftb(yarg_sl(2), yarg_z(1,0), yarg_d(0,0));
}

extern BuiltIn Y_fft_raw;

extern void cfft2(long , double *, long , long , long , void *);
void
Y_fft_raw(int n)
{
  if (n!=6) YError("fft_raw takes exactly 6 arguments");
  cfft2(yarg_sl(5), yarg_z(4,0), yarg_sl(3), yarg_sl(2), yarg_sl(1), 
    yarg_sp(0));
}

extern BuiltIn Y__roll2;

extern void roll2(void *, long , long , long , long , double *);
void
Y__roll2(int n)
{
  if (n!=6) YError("_roll2 takes exactly 6 arguments");
  roll2(yarg_sp(5), yarg_sl(4), yarg_sl(3), yarg_sl(2), 
    yarg_sl(1), yarg_d(0,0));
}


/*----------------begin graph.i */
extern BuiltIn Y_window;
extern BuiltIn Y_current_window;
extern BuiltIn Y_hcp_file;
extern BuiltIn Y_hcp_finish;
extern BuiltIn Y_fma;
extern BuiltIn Y_hcp;
extern BuiltIn Y_hcpon;
extern BuiltIn Y_hcpoff;
extern BuiltIn Y_redraw;
extern BuiltIn Y_palette;
extern BuiltIn Y_animate;
extern BuiltIn Y_plsys;
extern BuiltIn Y_plg;
extern BuiltIn Y_plm;
extern BuiltIn Y_plmesh;
extern BuiltIn Y_plc;
extern BuiltIn Y_contour;
extern BuiltIn Y_plv;
extern BuiltIn Y_plf;
extern BuiltIn Y_plfp;
extern BuiltIn Y_pli;
extern BuiltIn Y_pldj;
extern BuiltIn Y_plt;
extern BuiltIn Y_limits;
extern BuiltIn Y_logxy;
extern BuiltIn Y_gridxy;
extern BuiltIn Y_zoom_factor;
extern BuiltIn Y_unzoom;
extern BuiltIn Y_plq;
extern BuiltIn Y_pledit;
extern BuiltIn Y_pldefault;
extern BuiltIn Y_bytscl;
extern BuiltIn Y_mesh_loc;
extern BuiltIn Y_mouse;
extern BuiltIn Y_pause;
extern BuiltIn Y_rgb_read;
extern BuiltIn Y_viewport;
extern BuiltIn Y_raw_style;
extern BuiltIn Y__pl_init;
extern BuiltIn Y_keybd_focus;

/*----------------list include files */

static char *y0_includes[] = {
  "std.i",
  "matrix.i",
  "fft.i",
  "graph.i",
  0,
  0
};

/*----------------collect pointers and names */

static BuiltIn *y0_routines[] = {
  &Y_help,
  &Y_quit,
  &Y_system,
  &Y_yorick_init,
  &Y_set_path,
  &Y_get_path,
  &Y_get_pkgnames,
  &Y_set_site,
  &Y_yorick_stats,
  &Y_disassemble,
  &Y_reshape,
  &Y_eq_nocopy,
  &Y_array,
  &Y_structof,
  &Y_dimsof,
  &Y_orgsof,
  &Y_use_origins,
  &Y_sizeof,
  &Y_numberof,
  &Y_typeof,
  &Y_nameof,
  &Y_print,
  &Y_print_format,
  &Y_is_array,
  &Y_is_func,
  &Y_is_void,
  &Y_is_range,
  &Y_is_struct,
  &Y_is_stream,
  &Y_is_list,
  &Y_am_subroutine,
  &Y_sin,
  &Y_cos,
  &Y_tan,
  &Y_asin,
  &Y_acos,
  &Y_atan,
  &Y_sinh,
  &Y_cosh,
  &Y_tanh,
  &Y_exp,
  &Y_log,
  &Y_log10,
  &Y_sqrt,
  &Y_poly,
  &Y_ceil,
  &Y_floor,
  &Y_abs,
  &Y_sign,
  &Y_conj,
  &Y_random,
  &Y_random_seed,
  &Y_min,
  &Y_max,
  &Y_sum,
  &Y_avg,
  &Y_allof,
  &Y_anyof,
  &Y_noneof,
  &Y_nallof,
  &Y_where,
  &Y_merge,
  &Y_grow,
  &Y__,
  &Y_indgen,
  &Y_span,
  &Y_digitize,
  &Y_histogram,
  &Y_interp,
  &Y_integ,
  &Y_sort,
  &Y_transpose,
  &Y_strlen,
  &Y_strchar,
  &Y_strpart,
  &Y_strcase,
  &Y_strword,
  &Y__strtok,
  &Y_strglob,
  &Y_strfind,
  &Y_strgrep,
  &Y_streplace,
  &Y_open,
  &Y_popen,
  &Y_fflush,
  &Y_close,
  &Y_rename,
  &Y_remove,
  &Y_read,
  &Y_sread,
  &Y_rdline,
  &Y_write,
  &Y_swrite,
  &Y_bookmark,
  &Y_backup,
  &Y_include,
  &Y_require,
  &Y_plug_in,
  &Y_plug_dir,
  &Y_autoload,
  &Y_cd,
  &Y_lsdir,
  &Y_mkdir,
  &Y_rmdir,
  &Y_get_cwd,
  &Y_get_home,
  &Y_get_env,
  &Y_get_argv,
  &Y_get_member,
  &Y_read_clog,
  &Y__not_pdb,
  &Y__init_pdb,
  &Y__set_pdb,
  &Y__init_clog,
  &Y_dump_clog,
  &Y_get_primitives,
  &Y_save,
  &Y_restore,
  &Y__jr,
  &Y__jt,
  &Y__jc,
  &Y_add_record,
  &Y_add_variable,
  &Y_set_blocksize,
  &Y_set_filesize,
  &Y_get_vars,
  &Y_set_vars,
  &Y_get_addrs,
  &Y_get_times,
  &Y_get_ncycs,
  &Y_edit_times,
  &Y__read,
  &Y__write,
  &Y_add_member,
  &Y_install_struct,
  &Y_data_align,
  &Y_struct_align,
  &Y_add_next_file,
  &Y_error,
  &Y_exit,
  &Y_catch,
  &Y_batch,
  &Y_set_idler,
  &Y_maybe_prompt,
  &Y_funcdef,
  &Y_spawn,
  &Y_suspend,
  &Y_resume,
  &Y_after,
  &Y_timestamp,
  &Y_timer,
  &Y_symbol_def,
  &Y_symbol_set,
  &Y_dbexit,
  &Y_dbcont,
  &Y_dbret,
  &Y_dbskip,
  &Y_dbup,
  &Y_dbinfo,
  &Y_dbdis,
  &Y_dbauto,
  &Y__lst,
  &Y__cat,
  &Y__car,
  &Y__cdr,
  &Y__cpy,
  &Y__len,
  &Y__dgtsv,
  &Y__dgesv,
  &Y__dgetrf,
  &Y__dgecox,
  &Y__dgelx,
  &Y__dgelss,
  &Y__dgesvx,
  &Y_fft_init,
  &Y_fft_fraw,
  &Y_fft_braw,
  &Y_fft_raw,
  &Y__roll2,
  &Y_window,
  &Y_current_window,
  &Y_hcp_file,
  &Y_hcp_finish,
  &Y_fma,
  &Y_hcp,
  &Y_hcpon,
  &Y_hcpoff,
  &Y_redraw,
  &Y_palette,
  &Y_animate,
  &Y_plsys,
  &Y_plg,
  &Y_plm,
  &Y_plmesh,
  &Y_plc,
  &Y_contour,
  &Y_plv,
  &Y_plf,
  &Y_plfp,
  &Y_pli,
  &Y_pldj,
  &Y_plt,
  &Y_limits,
  &Y_logxy,
  &Y_gridxy,
  &Y_zoom_factor,
  &Y_unzoom,
  &Y_plq,
  &Y_pledit,
  &Y_pldefault,
  &Y_bytscl,
  &Y_mesh_loc,
  &Y_mouse,
  &Y_pause,
  &Y_rgb_read,
  &Y_viewport,
  &Y_raw_style,
  &Y__pl_init,
  &Y_keybd_focus,
  0
};

static void *y0_values[] = {
  0
};

static char *y0_names[] = {
  "help",
  "quit",
  "system",
  "yorick_init",
  "set_path",
  "get_path",
  "get_pkgnames",
  "set_site",
  "yorick_stats",
  "disassemble",
  "reshape",
  "eq_nocopy",
  "array",
  "structof",
  "dimsof",
  "orgsof",
  "use_origins",
  "sizeof",
  "numberof",
  "typeof",
  "nameof",
  "print",
  "print_format",
  "is_array",
  "is_func",
  "is_void",
  "is_range",
  "is_struct",
  "is_stream",
  "is_list",
  "am_subroutine",
  "sin",
  "cos",
  "tan",
  "asin",
  "acos",
  "atan",
  "sinh",
  "cosh",
  "tanh",
  "exp",
  "log",
  "log10",
  "sqrt",
  "poly",
  "ceil",
  "floor",
  "abs",
  "sign",
  "conj",
  "random",
  "random_seed",
  "min",
  "max",
  "sum",
  "avg",
  "allof",
  "anyof",
  "noneof",
  "nallof",
  "where",
  "merge",
  "grow",
  "_",
  "indgen",
  "span",
  "digitize",
  "histogram",
  "interp",
  "integ",
  "sort",
  "transpose",
  "strlen",
  "strchar",
  "strpart",
  "strcase",
  "strword",
  "_strtok",
  "strglob",
  "strfind",
  "strgrep",
  "streplace",
  "open",
  "popen",
  "fflush",
  "close",
  "rename",
  "remove",
  "read",
  "sread",
  "rdline",
  "write",
  "swrite",
  "bookmark",
  "backup",
  "include",
  "require",
  "plug_in",
  "plug_dir",
  "autoload",
  "cd",
  "lsdir",
  "mkdir",
  "rmdir",
  "get_cwd",
  "get_home",
  "get_env",
  "get_argv",
  "get_member",
  "read_clog",
  "_not_pdb",
  "_init_pdb",
  "_set_pdb",
  "_init_clog",
  "dump_clog",
  "get_primitives",
  "save",
  "restore",
  "_jr",
  "_jt",
  "_jc",
  "add_record",
  "add_variable",
  "set_blocksize",
  "set_filesize",
  "get_vars",
  "set_vars",
  "get_addrs",
  "get_times",
  "get_ncycs",
  "edit_times",
  "_read",
  "_write",
  "add_member",
  "install_struct",
  "data_align",
  "struct_align",
  "add_next_file",
  "error",
  "exit",
  "catch",
  "batch",
  "set_idler",
  "maybe_prompt",
  "funcdef",
  "spawn",
  "suspend",
  "resume",
  "after",
  "timestamp",
  "timer",
  "symbol_def",
  "symbol_set",
  "dbexit",
  "dbcont",
  "dbret",
  "dbskip",
  "dbup",
  "dbinfo",
  "dbdis",
  "dbauto",
  "_lst",
  "_cat",
  "_car",
  "_cdr",
  "_cpy",
  "_len",
  "_dgtsv",
  "_dgesv",
  "_dgetrf",
  "_dgecox",
  "_dgelx",
  "_dgelss",
  "_dgesvx",
  "fft_init",
  "fft_fraw",
  "fft_braw",
  "fft_raw",
  "_roll2",
  "window",
  "current_window",
  "hcp_file",
  "hcp_finish",
  "fma",
  "hcp",
  "hcpon",
  "hcpoff",
  "redraw",
  "palette",
  "animate",
  "plsys",
  "plg",
  "plm",
  "plmesh",
  "plc",
  "contour",
  "plv",
  "plf",
  "plfp",
  "pli",
  "pldj",
  "plt",
  "limits",
  "logxy",
  "gridxy",
  "zoom_factor",
  "unzoom",
  "plq",
  "pledit",
  "pldefault",
  "bytscl",
  "mesh_loc",
  "mouse",
  "pause",
  "rgb_read",
  "viewport",
  "raw_style",
  "_pl_init",
  "keybd_focus",
  0
};

/*----------------define package initialization function */

PLUG_EXPORT char *yk_yor(char ***,
                         BuiltIn ***, void ***, char ***);
static char *y0_pkgname = "yor";

char *
yk_yor(char ***ifiles,
       BuiltIn ***code, void ***data, char ***varname)
{
  *ifiles = y0_includes;
  *code = y0_routines;
  *data = y0_values;
  *varname = y0_names;
  return y0_pkgname;
}
