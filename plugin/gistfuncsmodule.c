/* Copyright (c) 1996, 1997, The Regents of the University of California.
 * All rights reserved.  See Legal.htm for full text and disclaimer. */
#include "Python.h"
#include "numpy/arrayobject.h"

#include <stdio.h>
#include <stdlib.h>

#define MAX_INTERP_DIMS 6

static PyObject *ErrorObject;

/* Define 2 macros for error handling:
   Py_Try(BOOLEAN)
   If BOOLEAN is FALSE, assume the error object has
   been set and return NULL

   Py_Assert(BOOLEAN,ERROBJ,MESS)
   If BOOLEAN is FALSE set the error object to
   ERROBJ, and the message to MESS

*/

static char *errstr = NULL;

#define Py_Try(BOOLEAN) {if (!(BOOLEAN)) return NULL;}
#define Py_Assert(BOOLEAN,ERROBJ,MESS) {if (!(BOOLEAN)) { \
					   PyErr_SetString((ERROBJ), (MESS)); \
					   return NULL;} \
				       }
#define A_DATA(a) (((PyArrayObject *)a)->data)
#define A_SIZE(a) PyArray_Size((PyObject *) a)
#define A_TYPE(a) (int)(((PyArrayObject *)a)->descr->type_num)
#define isARRAY(a) ((a) && PyArray_Check((PyArrayObject *)a))
#define A_NDIM(a) (((PyArrayObject *)a)->nd)
#define A_DIM(a,i) (((PyArrayObject *)a)->dimensions[i])
#define GET_ARR(ap,op,type,dim) \
  Py_Try(ap=(PyArrayObject *)PyArray_ContiguousFromObject(op,type,dim,dim))
#define GET_ARR2(ap,op,type,min,max) \
   Py_Try(ap=(PyArrayObject *)PyArray_ContiguousFromObject(op,type,min,max))
#define ERRSS(s) ((PyObject *)(PyErr_SetString(ErrorObject,s),(void *)0))
#define SETERR(s) if(!PyErr_Occurred()) ERRSS(errstr ? errstr : s)
#define DECREF_AND_ZERO(p) do{Py_XDECREF(p);p=0;}while(0)

/* ----------------------------------------------------- */

static int mxx(int *i, int len)
{
	/* find the index of the maximum element of an integer array */
	int mx = 0, max = i[0];
	int j;
	for (j = 1; j < len; j++)
		if (i[j] > max) {
			max = i[j];
			mx = j;
		}
	return mx;
}

static int mnx(int *i, int len)
{
	/* find the index of the minimum element of an integer array */
	int mn = 0, min = i[0];
	int j;
	for (j = 1; j < len; j++)
		if (i[j] < min) {
			min = i[j];
			mn = j;
		}
	return mn;
}

static char arr_array_set__doc__[] =
    "array_set accepts three arguments. The first is an array of\n\
numerics (Python characters, integers, or floats), and the\n\
third is of the same type. The second is an array of integers\n\
which are valid subscripts into the first. The third array\n\
must be at least long enough to supply all the elements\n\
called for by the subscript array. (It can also be a scalar,\n\
in which case its value will be broadcast.) The result is that\n\
elements of the third array are assigned in order to elements\n\
of the first whose subscripts are elements of the second.\n\
  arr_array_set (vals1, indices, vals2)\n\
is equivalent to the Yorick assignment vals1 (indices) = vals2.\n\
I have generalized this so that the source and target arrays\n\
may be two dimensional; the second dimensions must match.\n\
Then the array of subscripts is assumed to apply to the first\n\
subscript only of the target. The target had better be contiguous.";

static PyObject *arr_array_set(PyObject * self, PyObject * args)
{
	PyObject *tararg, *subsarg, *srcarg;
	PyArrayObject *tararr, *subsarr, *srcarr = NULL;
	double *dtar, *dsrc, ds = 0.0;
	float *ftar, *fsrc, fs = 0.0;
	char *ctar, *csrc, cs = '\0';
	unsigned char *utar, *usrc, us = 0;
	int *itar, *isrc, *isubs;
	long *ltar, *lsrc;
	long is = 0;
	int i, j, len, mn, mx;
	int scalar_source = 0;
	char scalar_type = 'x';
	int nd, d1;		/* number of dimensions and value of second dim. */

	Py_Try(PyArg_ParseTuple(args, "OOO", &tararg, &subsarg, &srcarg));
	d1 = 1;
	nd = A_NDIM(tararg);
	if (PyFloat_Check(srcarg)) {
		scalar_source = 1;
		scalar_type = 'f';
		ds = PyFloat_AS_DOUBLE(srcarg);
	} else if (PyInt_Check(srcarg)) {
		scalar_source = 1;
		scalar_type = 'i';
		is = PyInt_AS_LONG(srcarg);
	} else if (PyString_Check(srcarg)) {
		scalar_source = 1;
		scalar_type = 'c';
		cs = PyString_AS_STRING(srcarg)[0];
	} else if (nd == 2) {
		d1 = A_DIM(tararg, 1);
		if (A_NDIM(srcarg) != 2 || A_DIM(srcarg, 1) != d1) {
			SETERR
			    ("array_set: dimension mismatch between source and target.");
			return NULL;
		}
	} else if (nd != 1) {
		SETERR("array_set: target must have one or two dimensions.");
		return NULL;
	}
	GET_ARR(subsarr, subsarg, PyArray_INT, 1);
	isubs = (int *)A_DATA(subsarr);
	len = A_SIZE(subsarr);
	mn = mnx(isubs, len);
	if (isubs[mn] < 0) {
		SETERR("array_set: negative subscript specified.");
		Py_DECREF(subsarr);
		return NULL;
	}
	mx = mxx(isubs, len);
	switch (A_TYPE(tararg)) {
	case PyArray_UBYTE:
		GET_ARR(tararr, tararg, PyArray_UBYTE, nd);
		if (d1 * isubs[mx] > A_SIZE(tararr)) {
			SETERR("array_set: a subscript is out of range.");
			Py_DECREF(subsarr);
			Py_DECREF(tararr);
			return NULL;
		}
		if (!scalar_source) {
			GET_ARR(srcarr, srcarg, PyArray_UBYTE, 1);
			if (A_SIZE(srcarr) < d1 * len) {
				SETERR
				    ("array_set: source is too short for number of subscripts.");
				Py_DECREF(subsarr);
				Py_DECREF(tararr);
				Py_DECREF(srcarr);
				return NULL;
			}
			utar = (unsigned char *)A_DATA(tararr);
			usrc = (unsigned char *)A_DATA(srcarr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					utar[d1 * isubs[i] + j] =
					    usrc[i * d1 + j];
		} else {
			switch (scalar_type) {
			case 'c':
				us = (unsigned char)cs;
				break;
			case 'i':
				us = (unsigned char)is;
				break;
			case 'f':
				us = (unsigned char)ds;
				break;
			}
			utar = (unsigned char *)A_DATA(tararr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					utar[d1 * isubs[i] + j] = us;
		}
		break;
	case PyArray_CHAR:
		GET_ARR(tararr, tararg, PyArray_CHAR, nd);
		if (d1 * isubs[mx] > A_SIZE(tararr)) {
			SETERR("array_set: a subscript is out of range.");
			Py_DECREF(subsarr);
			Py_DECREF(tararr);
			return NULL;
		}
		if (!scalar_source) {
			GET_ARR(srcarr, srcarg, PyArray_CHAR, nd);
			if (A_SIZE(srcarr) < d1 * len) {
				SETERR
				    ("array_set: source is too short for number of subscripts.");
				Py_DECREF(subsarr);
				Py_DECREF(tararr);
				Py_DECREF(srcarr);
				return NULL;
			}
			ctar = (char *)A_DATA(tararr);
			csrc = (char *)A_DATA(srcarr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					ctar[isubs[i] * d1 + j] =
					    csrc[i * d1 + j];
		} else {
			switch (scalar_type) {
			case 'c':
				break;
			case 'i':
				cs = (unsigned char)is;
				break;
			case 'f':
				cs = (unsigned char)ds;
				break;
			}
			ctar = (char *)A_DATA(tararr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					ctar[d1 * isubs[i] + j] = cs;
		}
		break;
	case PyArray_INT:
		GET_ARR(tararr, tararg, PyArray_INT, nd);
		if (isubs[mx] * d1 > A_SIZE(tararr)) {
			SETERR("array_set: a subscript is out of range.");
			Py_DECREF(subsarr);
			Py_DECREF(tararr);
			return NULL;
		}
		if (!scalar_source) {
			GET_ARR(srcarr, srcarg, PyArray_INT, nd);
			if (A_SIZE(srcarr) < len * d1) {
				SETERR
				    ("array_set: source is too short for number of subscripts.");
				Py_DECREF(subsarr);
				Py_DECREF(tararr);
				Py_DECREF(srcarr);
				return NULL;
			}
			itar = (int *)A_DATA(tararr);
			isrc = (int *)A_DATA(srcarr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					itar[isubs[i] * d1 + j] =
					    isrc[i * d1 + j];
		} else {
			switch (scalar_type) {
			case 'c':
				is = (long)cs;
				break;
			case 'i':
				break;
			case 'f':
				is = (long)ds;
				break;
			}
			itar = (int *)A_DATA(tararr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					itar[d1 * isubs[i] + j] = is;
		}
		break;
	case PyArray_LONG:
		GET_ARR(tararr, tararg, PyArray_LONG, nd);
		if (isubs[mx] * d1 > A_SIZE(tararr)) {
			SETERR("array_set: a subscript is out of range.");
			Py_DECREF(subsarr);
			Py_DECREF(tararr);
			return NULL;
		}
		if (!scalar_source) {
			GET_ARR(srcarr, srcarg, PyArray_LONG, nd);
			if (A_SIZE(srcarr) < len * d1) {
				SETERR
				    ("array_set: source is too short for number of subscripts.");
				Py_DECREF(subsarr);
				Py_DECREF(tararr);
				Py_DECREF(srcarr);
				return NULL;
			}
			ltar = (long *)A_DATA(tararr);
			lsrc = (long *)A_DATA(srcarr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					ltar[isubs[i] * d1 + j] =
					    lsrc[i * d1 + j];
		} else {
			switch (scalar_type) {
			case 'c':
				is = (long)cs;
				break;
			case 'i':
				break;
			case 'f':
				is = (long)ds;
				break;
			}
			ltar = (long *)A_DATA(tararr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					ltar[d1 * isubs[i] + j] = is;
		}
		break;
	case PyArray_FLOAT:
		GET_ARR(tararr, tararg, PyArray_FLOAT, nd);
		if (isubs[mx] * d1 > A_SIZE(tararr)) {
			SETERR("array_set: a subscript is out of range.");
			Py_DECREF(subsarr);
			Py_DECREF(tararr);
			return NULL;
		}
		if (!scalar_source) {
			GET_ARR(srcarr, srcarg, PyArray_FLOAT, nd);
			if (A_SIZE(srcarr) < len * d1) {
				SETERR
				    ("array_set: source is too short for number of subscripts.");
				Py_DECREF(subsarr);
				Py_DECREF(tararr);
				Py_DECREF(srcarr);
				return NULL;
			}
			ftar = (float *)A_DATA(tararr);
			fsrc = (float *)A_DATA(srcarr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					ftar[isubs[i] * d1 + j] =
					    fsrc[i * d1 + j];
		} else {
			switch (scalar_type) {
			case 'c':
				fs = (float)cs;
				break;
			case 'i':
				fs = (float)is;
				break;
			case 'f':
				fs = (float)ds;
				break;
			}
			ftar = (float *)A_DATA(tararr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					ftar[d1 * isubs[i] + j] = fs;
		}
		break;
	case PyArray_DOUBLE:
		GET_ARR(tararr, tararg, PyArray_DOUBLE, nd);
		if (isubs[mx] * d1 > A_SIZE(tararr)) {
			SETERR("array_set: a subscript is out of range.");
			Py_DECREF(subsarr);
			Py_DECREF(tararr);
			return NULL;
		}
		if (!scalar_source) {
			GET_ARR(srcarr, srcarg, PyArray_DOUBLE, nd);
			if (A_SIZE(srcarr) < len * d1) {
				SETERR
				    ("array_set: source is too short for number of subscripts.");
				Py_DECREF(subsarr);
				Py_DECREF(tararr);
				Py_DECREF(srcarr);
				return NULL;
			}
			dtar = (double *)A_DATA(tararr);
			dsrc = (double *)A_DATA(srcarr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					dtar[isubs[i] * d1 + j] =
					    dsrc[i * d1 + j];
		} else {
			switch (scalar_type) {
			case 'c':
				ds = (double)cs;
				break;
			case 'i':
				ds = (double)is;
				break;
			case 'f':
				break;
			}
			dtar = (double *)A_DATA(tararr);
			for (i = 0; i < len; i++)
				for (j = 0; j < d1; j++)
					dtar[d1 * isubs[i] + j] = ds;
		}
		break;
	default:
		SETERR("array_set: Not implemented for this type.");
		Py_DECREF(subsarr);
		return NULL;
	}

	Py_DECREF(subsarr);
	Py_DECREF(tararr);
	Py_XDECREF(srcarr);
	Py_INCREF(Py_None);
	return Py_None;
}

static void _adjust(double *k, int *list, int i, int n)
{
	/* adjust the binary tree k with root list [i] to satisfy the heap
	 * property. The left and right subtrees of list [i], with roots
	 * list [2 * i + 1] and list [2 * i + 2], already satisfy the heap
	 * property. No node has index greater than n.
	 * Horowitz & Sahni, p. 358.                                     */
	double kt;		/* will contain root value which may need to be moved */
	int kj,			/* root value is at kj position in list               */
	 j, lowj;		/* parent of current j node                           */

	kj = list[i];
	kt = k[kj];
	j = 2 * i + 1;
	lowj = i;
	while (j < n) {
		if (j < n - 1 && k[list[j]] < k[list[j + 1]])
			/* make list [j] point to the larger child */
			j = j + 1;
		if (kt >= k[list[j]]) {
			list[lowj] = kj;
			return;
		}
		list[lowj] = list[j];
		lowj = j;
		j = 2 * j + 1;
	}
	list[lowj] = kj;
}

static char arr_index_sort__doc__[] =
    "index_sort accepts one array of some numerical type and returns\n\
an integer array of the same length whose entries are the\n\
subscripts of the elements of the original array arranged\n\
in increasing order. I chose to use heap sort because its\n\
worst behavior is n*log(n), unlike quicksort, whose worst\n\
behavior is n**2.";

static PyObject *arr_index_sort(PyObject * self, PyObject * args)
{

	PyObject *list;
	PyArrayObject *alist, *ilist;
	double *data;
	int i, *isubs, itmp;
	npy_intp len;

	Py_Try(PyArg_ParseTuple(args, "O", &list));
	GET_ARR(alist, list, PyArray_DOUBLE, 1);
	len = A_SIZE(alist);
	Py_Try(ilist =
	       (PyArrayObject *) PyArray_SimpleNew(1, &len, PyArray_INT));
	isubs = (int *)A_DATA(ilist);
	for (i = 0; i < len; i++)
		isubs[i] = i;

	data = (double *)A_DATA(alist);
	/* now do heap sort on subscripts */
	for (i = len / 2; i >= 0; i--) {
		_adjust(data, isubs, i, len);
	}
	for (i = len - 1; i >= 0; i--) {
		itmp = isubs[i];
		isubs[i] = isubs[0];
		isubs[0] = itmp;
		_adjust(data, isubs, 0, i);
	}

	Py_DECREF(alist);
	return (PyObject *) ilist;
}

static int _binary_search(double dval, double dlist[], int len)
{
	/* binary_search accepts three arguments: a numeric value and
	 * a numeric array and its length. It assumes that the array is sorted in
	 * increasing order. It returns the index of the array's
	 * largest element which is <= the value. It will return -1 if
	 * the value is less than the least element of the array. */
	/* self is not used */
	int bottom, top, middle, result;

	if (dval < dlist[0])
		result = -1;
	else {
		bottom = 0;
		top = len - 1;
		while (bottom < top) {
			middle = (top + bottom) / 2;
			if (dlist[middle] < dval)
				bottom = middle + 1;
			else if (dlist[middle] > dval)
				top = middle - 1;
			else
				return middle;
		}
		if (dlist[bottom] > dval)
			result = bottom - 1;
		else
			result = bottom;
	}

	return result;
}

static int _binary_searchf(float dval, float dlist[], int len)
{
	/* binary_search accepts three arguments: a numeric value and
	 * a numeric array and its length. It assumes that the array is sorted in
	 * increasing order. It returns the index of the array's
	 * largest element which is <= the value. It will return -1 if
	 * the value is less than the least element of the array. */
	/* self is not used */
	int bottom, top, middle, result;

	if (dval < dlist[0])
		result = -1;
	else {
		bottom = 0;
		top = len - 1;
		while (bottom < top) {
			middle = (top + bottom) / 2;
			if (dlist[middle] < dval)
				bottom = middle + 1;
			else if (dlist[middle] > dval)
				top = middle - 1;
			else
				return middle;
		}
		if (dlist[bottom] > dval)
			result = bottom - 1;
		else
			result = bottom;
	}

	return result;
}

/* return float, rather than double */

static PyObject *arr_interpf(PyObject * self, PyObject * args)
{
	/* interp (y, x, z) treats (x, y) as a piecewise linear function
	 * whose value is y [0] for x < x [0] and y [len (y) -1] for x >
	 * x [len (y) -1]. An array of floats the same length as z is
	 * returned, whose values are ordinates for the corresponding z
	 * abscissae interpolated into the piecewise linear function.         */
	/* self is not used */
	PyObject *oy, *ox, *oz;
	PyArrayObject *ay, *ax, *az, *_interp;
	float *dy, *dx, *dz, *dres, *slopes;
	int leny, lenz, i, left;

	PyObject *tpo = Py_None;	/* unused argument, we've already parsed it */

	Py_Try(PyArg_ParseTuple(args, "OOO|O", &oy, &ox, &oz, &tpo));
	GET_ARR(ay, oy, PyArray_FLOAT, 1);
	GET_ARR(ax, ox, PyArray_FLOAT, 1);
	if ((leny = A_SIZE(ay)) != A_SIZE(ax)) {
		SETERR("interp: x and y are not the same length.");
		Py_DECREF(ay);
		Py_DECREF(ax);
		return NULL;
	}
	GET_ARR2(az, oz, PyArray_FLOAT, 1, MAX_INTERP_DIMS);
	lenz = A_SIZE(az);
	dy = (float *)A_DATA(ay);
	dx = (float *)A_DATA(ax);
	dz = (float *)A_DATA(az);
	/* create output array with same size as 'Z' input array */
	Py_Try(_interp = (PyArrayObject *) PyArray_SimpleNew
	       (A_NDIM(az), az->dimensions, PyArray_FLOAT));
	dres = (float *)A_DATA(_interp);
	slopes = (float *)malloc((leny - 1) * sizeof(float));
	for (i = 0; i < leny - 1; i++) {
		slopes[i] = (dy[i + 1] - dy[i]) / (dx[i + 1] - dx[i]);
	}
	for (i = 0; i < lenz; i++) {
		left = _binary_searchf(dz[i], dx, leny);
		if (left < 0)
			dres[i] = dy[0];
		else if (left >= leny - 1)
			dres[i] = dy[leny - 1];
		else
			dres[i] = slopes[left] * (dz[i] - dx[left]) + dy[left];
	}

	free(slopes);
	Py_DECREF(ay);
	Py_DECREF(ax);
	Py_DECREF(az);
	return PyArray_Return(_interp);
}

static char arr_interp__doc__[] =
    "interp(y, x, z [,resulttypecode]) = y(z) interpolated by treating y(x)\n\
as piecewise fcn.\n\
whose value is y [0] for x < x [0] and y [len (y) -1] for x >\n\
x [len (y) -1]. An array of floats the same length as z is\n\
returned, whose values are ordinates for the corresponding z\n\
abscissae interpolated into the piecewise linear function.";

static PyObject *arr_interp(PyObject * self, PyObject * args)
{
	PyObject *oy, *ox, *oz;
	PyArrayObject *ay, *ax, *az, *_interp;
	double *dy, *dx, *dz, *dres, *slopes;
	int leny, lenz, i, left;
	PyObject *tpo = Py_None;
	char type_char = 'd';
	char *type = &type_char;

	Py_Try(PyArg_ParseTuple(args, "OOO|O", &oy, &ox, &oz, &tpo));
	if (tpo != Py_None) {
		type = PyString_AsString(tpo);
		if (!type)
			return NULL;
		if (!*type)
			type = &type_char;
	}
	if (*type == 'f') {
		return arr_interpf(self, args);
	} else if (*type != 'd') {
		SETERR("interp: unimplemented typecode.");
		return NULL;
	}
	GET_ARR(ay, oy, PyArray_DOUBLE, 1);
	GET_ARR(ax, ox, PyArray_DOUBLE, 1);
	if ((leny = A_SIZE(ay)) != A_SIZE(ax)) {
		SETERR("interp: x and y are not the same length.");
		Py_DECREF(ay);
		Py_DECREF(ax);
		return NULL;
	}
	GET_ARR2(az, oz, PyArray_DOUBLE, 1, MAX_INTERP_DIMS);
	lenz = A_SIZE(az);
	dy = (double *)A_DATA(ay);
	dx = (double *)A_DATA(ax);
	dz = (double *)A_DATA(az);
	/* create output array with same size as 'Z' input array */
	Py_Try(_interp = (PyArrayObject *) PyArray_SimpleNew
	       (A_NDIM(az), az->dimensions, PyArray_DOUBLE));
	dres = (double *)A_DATA(_interp);
	slopes = (double *)malloc((leny - 1) * sizeof(double));
	for (i = 0; i < leny - 1; i++) {
		slopes[i] = (dy[i + 1] - dy[i]) / (dx[i + 1] - dx[i]);
	}
	for (i = 0; i < lenz; i++) {
		left = _binary_search(dz[i], dx, leny);
		if (left < 0)
			dres[i] = dy[0];
		else if (left >= leny - 1)
			dres[i] = dy[leny - 1];
		else
			dres[i] = slopes[left] * (dz[i] - dx[left]) + dy[left];
	}

	free(slopes);
	Py_DECREF(ay);
	Py_DECREF(ax);
	Py_DECREF(az);
	return PyArray_Return(_interp);
}

static char arr_zmin_zmax__doc__[] =
    "zmin_zmax (z, ireg) returns a 2-tuple which consists\n\
of the minimum and maximum values of z on the portion of the\n\
mesh where ireg is not zero. z is a 2d array of Float and ireg\n\
is an array of the same shape of Integer. By convention the first\n\
row and column of ireg are zero, and the remaining entries are\n\
used to determine which region each cell belongs to. A zero\n\
entry says that this cell is excluded from the mesh.";

static PyObject *arr_zmin_zmax(PyObject * self, PyObject * args)
{
	PyObject *zobj, *iregobj;
	PyArrayObject *zarr, *iregarr;
	double *z, zmin = 0.0, zmax = 0.0;
	int *ireg;
	int have_min_max = 0;
	int i, j, k, n, m;

	Py_Try(PyArg_ParseTuple(args, "OO", &zobj, &iregobj));
	GET_ARR(zarr, zobj, PyArray_DOUBLE, 2);
	if (!(iregarr = (PyArrayObject *) PyArray_ContiguousFromObject(iregobj,
								       PyArray_INT,
								       2, 2))) {
		Py_DECREF(zarr);
		return NULL;
	}
	n = A_DIM(iregarr, 0);
	m = A_DIM(iregarr, 1);
	if (n != A_DIM(zarr, 0) || m != A_DIM(zarr, 1)) {
		SETERR("zmin_zmax: z and ireg do not have the same shape.");
		Py_DECREF(iregarr);
		Py_DECREF(zarr);
		return NULL;
	}
	ireg = (int *)A_DATA(iregarr);
	z = (double *)A_DATA(zarr);
	k = 0;			/* k is i * m + j */
	for (i = 0; i < n; i++) {
		for (j = 0; j < m; j++) {
			if ((ireg[k] != 0) ||
			    (i != n - 1 && j != m - 1 &&
			     (ireg[k + m] != 0 || ireg[k + 1] != 0
			      || ireg[k + m + 1] != 0))) {
				if (!have_min_max) {
					have_min_max = 1;
					zmin = zmax = z[k];
				} else {
					if (z[k] < zmin)
						zmin = z[k];
					else if (z[k] > zmax)
						zmax = z[k];
				}
			}
			k++;
		}
	}
	Py_DECREF(iregarr);
	Py_DECREF(zarr);
	if (!have_min_max) {
		SETERR("zmin_zmax: unable to calculate zmin and zmax!");
		return NULL;
	}
	return Py_BuildValue("dd", zmin, zmax);
}

static char arr_reverse__doc__[] =
    "reverse (x, n) returns a PyFloat Matrix the same size and shape as\n\
x, but with the elements along the nth dimension reversed.\n\
x must be two-dimensional.";

static PyObject *arr_reverse(PyObject * self, PyObject * args)
{
	PyObject *ox;
	int n;
	PyArrayObject *ax, *ares;
	double *dx, *dres;
	int d0, d1;
	int i, jl, jh;
	npy_intp dims[2];
	Py_Try(PyArg_ParseTuple(args, "Oi", &ox, &n));
	if (n != 0 && n != 1) {
		SETERR("reverse: Second argument must be 0 or 1.");
		return NULL;
	}
	GET_ARR(ax, ox, PyArray_DOUBLE, 2);
	dx = (double *)A_DATA(ax);
	d0 = dims[0] = A_DIM(ax, 0);
	d1 = dims[1] = A_DIM(ax, 1);
	Py_Try(ares =
	       (PyArrayObject *) PyArray_SimpleNew(2, dims, PyArray_DOUBLE));
	dres = (double *)A_DATA(ares);
	if (n == 0)		/* reverse the columns */
		for (i = 0; i < d1; i++) {
			for (jl = i, jh = (d0 - 1) * d1 + i; jl < jh;
			     jl += d1, jh -= d1) {
				dres[jl] = dx[jh];
				dres[jh] = dx[jl];
			}
			if (jl == jh)
				dres[jl] = dx[jl];
	} else			/* reverse the rows */
		for (i = 0; i < d0; i++) {
			for (jl = i * d1, jh = (i + 1) * d1 - 1; jl < jh;
			     jl += 1, jh -= 1) {
				dres[jl] = dx[jh];
				dres[jh] = dx[jl];
			}
			if (jl == jh)
				dres[jl] = dx[jl];
		}

	Py_DECREF(ax);
	return PyArray_Return(ares);
}

static char arr_span__doc__[] =
    "span (lo, hi, num, d2 = 0) returns an array of num equally\n\
spaced PyFloats starting with lo and ending with hi. if d2 is\n\
not zero, it will return a two-dimensional array, each of the\n\
d2 rows of which is the array of equally spaced numbers.";

static PyObject *arr_span(PyObject * self, PyObject * args)
{
	int d2 = 0;
	npy_intp num;
	npy_intp dims[2];
	double lo, hi, *drow, *dres;
	int i, j, id2;
	PyArrayObject *arow, *ares;

	Py_Try(PyArg_ParseTuple(args, "ddi|i", &lo, &hi, &num, &d2));
	dims[1] = num;
	dims[0] = d2;

	Py_Try(arow =
	       (PyArrayObject *) PyArray_SimpleNew(1, &num, PyArray_DOUBLE));

	drow = (double *)A_DATA(arow);

	for (i = 0; i < num; i++)
		drow[i] = lo + ((double)i) * (hi - lo) / ((double)(num - 1));
	if (d2 == 0)
		return PyArray_Return(arow);
	else {
		Py_Try
		    (ares =
		     (PyArrayObject *) PyArray_SimpleNew(2, dims,
							 PyArray_DOUBLE));
		dres = (double *)A_DATA(ares);
		for (id2 = 0; id2 < num * d2; id2 += num)
			for (j = 0; j < num; j++)
				dres[id2 + j] = drow[j];
		Py_DECREF(arow);
	}

	return PyArray_Return(ares);
}

static char arr_nz__doc__[] = "nz_ (x): x is an array of unsigned bytes. If x\n\
ends with a bunch of zeros, this returns with the index of\n\
the first zero element after the last nonzero element.\n\
It returns the length of the array if its last element\n\
is nonzero. This is essentially the 'effective length'\n\
of the array.";

static PyObject *arr_nz(PyObject * self, PyObject * args)
{
	int i, len;
	unsigned char *cdat;
	PyObject *odat;
	PyArrayObject *adat;

	Py_Try(PyArg_ParseTuple(args, "O", &odat));
	GET_ARR(adat, odat, PyArray_UBYTE, 1);
	cdat = (unsigned char *)A_DATA(adat);
	len = A_SIZE(adat);
	for (i = len; i > 0; i--)
		if (cdat[i - 1] != (unsigned char)0)
			break;
	Py_DECREF(adat);
	return PyInt_FromLong((long)i);
}

static char arr_find_mask__doc__[] =
    "find_mask (fs, node_edges): This function is used to calculate\n\
a mask whose corresponding entry is 1 precisely if an edge\n\
of a cell is cut by an isosurface, i. e., if the function\n\
fs is one on one of the two vertices of an edge and zero\n\
on the other (fs = 1 represents where some function on\n\
the mesh was found to be negative by the calling routine).\n\
fs is ntotal by nv, where nv is the number of vertices\n\
of a cell (4 for a tetrahedren, 5 for a pyramid, 6 for a prism).\n\
node_edges is a nv by ne array, where ne is the number of\n\
edges on a cell (6 for a tet, 8 for a pyramid, 9 for a prism).\n\
The entries in each row are 1 precisely if the corresponding edge\n\
is incident on the vertex. The exclusive or of the rows\n\
which correspond to nonzero entries in fs contains 1 in\n\
entries corresponding to edges where fs has opposite values\n\
on the vertices.";

static PyObject *arr_find_mask(PyObject * self, PyObject * args)
{
	PyObject *fso, *node_edgeso;
	PyArrayObject *fsa, *node_edgesa, *maska;
	int *fs, *node_edges, *mask;
	int i, j, k, l, ll, ifs, imask, ntotal, ne, nv;
	npy_intp ans_size;

	Py_Try(PyArg_ParseTuple(args, "OO", &fso, &node_edgeso));
	GET_ARR(fsa, fso, PyArray_INT, 2);
	GET_ARR(node_edgesa, node_edgeso, PyArray_INT, 2);
	fs = (int *)A_DATA(fsa);
	node_edges = (int *)A_DATA(node_edgesa);
	ntotal = A_DIM(fsa, 0);
	nv = A_DIM(fsa, 1);
	if (nv != A_DIM(node_edgesa, 0)) {
		SETERR
		    ("2nd dimension of 1st arg and 1st dimension of 2nd not equal.");
		Py_DECREF(fsa);
		Py_DECREF(node_edgesa);
		return (NULL);
	}
	ne = A_DIM(node_edgesa, 1);
	ans_size = ntotal * ne;
	Py_Try(maska = (PyArrayObject *) PyArray_SimpleNew
	       (1, &ans_size, PyArray_INT));
	mask = (int *)A_DATA(maska);

	for (i = 0, ifs = 0, imask = 0; i < ntotal; i++, imask += ne, ifs += nv) {
		for (j = ifs, k = 0; k < nv; j++, k++) {
			if (fs[j]) {
				for (l = imask, ll = 0; ll < ne; l++, ll++) {
					mask[l] ^= node_edges[j % nv * ne + ll];
				}
			}
		}
	}

	return PyArray_Return(maska);

}

/* Data for construct3 and walk3 */
static int start_face4[] = { 0, 0, 1, 0, 2, 1 };
static int start_face5[] = { 0, 0, 1, 2, 0, 1, 2, 3 };
static int start_face6[] = { 1, 1, 0, 0, 2, 2, 0, 0, 1 };
static int start_face8[] = { 0, 1, 0, 1, 0, 1, 0, 1, 2, 3, 2, 3 };

static int *start_face[4] = { start_face4, start_face5, start_face6,
	start_face8
};

static int ef0[] = { 0, 1 };
static int ef1[] = { 0, 2 };
static int ef2[] = { 0, 3 };
static int ef3[] = { 0, 4 };
static int ef4[] = { 0, 5 };
static int ef5[] = { 1, 2 };
static int ef6[] = { 1, 3 };
static int ef7[] = { 1, 4 };
static int ef8[] = { 1, 5 };
static int ef9[] = { 2, 3 };
static int ef10[] = { 2, 4 };
static int ef11[] = { 2, 5 };
static int ef12[] = { 3, 4 };
static int ef13[] = { 3, 5 };
static int *edge_faces4[] = { ef0, ef1, ef5, ef2, ef9, ef6 };
static int *edge_faces5[] = { ef2, ef0, ef5, ef9, ef3, ef7, ef10, ef12 };
static int *edge_faces6[] = { ef6, ef7, ef2, ef3, ef9, ef10, ef0, ef1, ef5 };

static int *edge_faces8[] = { ef1, ef5, ef2, ef6, ef3, ef7, ef4, ef8, ef10,
	ef12, ef11, ef13
};

static int **edge_faces[] = { edge_faces4, edge_faces5, edge_faces6,
	edge_faces8
};

static int fe40[] = { 0, 1, 3 };
static int fe41[] = { 0, 5, 2 };
static int fe42[] = { 1, 2, 4 };
static int fe43[] = { 3, 4, 5 };
static int *face_edges4[] = { fe40, fe41, fe42, fe43 };
static int fe50[] = { 0, 1, 4 };
static int fe51[] = { 1, 2, 5 };
static int fe52[] = { 2, 3, 6 };
static int fe53[] = { 0, 7, 3 };
static int fe54[] = { 4, 5, 6, 7 };
static int *face_edges5[] = { fe50, fe51, fe52, fe53, fe54 };
static int fe60[] = { 2, 7, 3, 6 };
static int fe61[] = { 0, 6, 1, 8 };
static int fe62[] = { 4, 8, 5, 7 };
static int fe63[] = { 0, 4, 2 };
static int fe64[] = { 1, 3, 5 };
static int *face_edges6[] = { fe60, fe61, fe62, fe63, fe64 };
static int fe80[] = { 0, 6, 2, 4 };
static int fe81[] = { 1, 5, 3, 7 };
static int fe82[] = { 0, 8, 1, 10 };
static int fe83[] = { 2, 11, 3, 9 };
static int fe84[] = { 4, 9, 5, 8 };
static int fe85[] = { 6, 10, 7, 11 };
static int *face_edges8[] = { fe80, fe81, fe82, fe83, fe84, fe85 };

static int **face_edges[] = { face_edges4, face_edges5, face_edges6,
	face_edges8
};

static int lens4[] = { 3, 3, 3, 3 };
static int lens5[] = { 3, 3, 3, 3, 4 };
static int lens6[] = { 4, 4, 4, 3, 3 };
static int lens8[] = { 4, 4, 4, 4, 4, 4 };
static int *lens[] = { lens4, lens5, lens6, lens8 };

static int no_edges[4] = { 6, 8, 9, 12 };

/* static int no_verts [4] = {4, 5, 6, 8} ; */
static int powers[4] = { 14, 30, 62, 254 };

/* FILE * dbg; */

static void walk3(int *permute, int *mask, int itype, int pt)
{
	int split, splits[12],
	    /* list [12] , */
	 nlist, edge = 0, face, i, j, *ttry, lttry, now;

	for (i = 0; i < 12; i++)
		splits[i] = 0;
	/* list = mask.nonzero () */
	for (i = 0, nlist = 0; i < no_edges[itype]; i++)
		if (mask[i]) {

			/* list [nlist++] = i ; */
			nlist++;	/* instead */

			if (nlist == 1)
				edge = i;
		}
	split = 0;
	face = start_face[itype][edge];
	for (i = 0; i < nlist - 1; i++) {
		/* record this edge */
		permute[edge * pt] = i;
		splits[edge] = split;
		mask[edge] = 0;
		/* advance to next edge */
		ttry = face_edges[itype][face];
		lttry = lens[itype][face];
		now = 0;
		for (j = 1; j < lttry; j++)
			if (abs(ttry[now] - edge) > abs(ttry[j] - edge))
				now = j;
		now++;
		/* test opposite edge first (make X, never // or \\) */
		edge = ttry[(now + 1) % lttry];
		if (!mask[edge]) {
			/* otherwise one or the other opposite edges must be set */
			edge = ttry[now % lttry];
			if (!mask[edge]) {
				edge = ttry[(now + 2) % lttry];
				if (!mask[edge]) {
					split++;
					for (edge = 0; edge < no_edges[itype];
					     edge++) {
						if (mask[edge] != 0) {
							break;
						}
					}
				}
			}
		}
		ttry = edge_faces[itype][edge];
		face = (face == ttry[0]) ? ttry[1] : ttry[0];
	}
	permute[edge * pt] = nlist - 1;
	splits[edge] = split;
	mask[edge] = 0;
	if (split != 0)
		for (i = 0, j = 0; i < no_edges[itype]; i++, j += pt) {
			permute[j] += no_edges[itype] * splits[i];
		}
	return;
}

static char arr_construct3__doc__[] = "\
construct3 (mask, itype) computes how the cut\n\
edges of a particular type of cell must be ordered so\n\
that the polygon of intersection can be drawn correctly.\n\
itype = 0 for tetrahedra; 1 for pyramids; 2 for prisms;\n\
3 for hexahedra. Suppose nv is the number of vertices\n\
of the cell type, and ne is the number of edges. Mask\n\
has been ravelled so that it was flat, originally it\n\
had 2**nv-2 rows, each with ne entries. Each row is\n\
ne long, and has an entry of 1 corresponding to each\n\
edge that is cut when the set of vertices corresponding\n\
to the row index has negative values. (The binary number\n\
for the row index + 1 has a one in position i if vertex\n\
i has a negative value.) The return array permute is\n\
ne by 2**nv-2, and the rows of permute tell how\n\
the edges should be ordered to draw the polygon properly.";

static PyObject *arr_construct3(PyObject * self, PyObject * args)
{
	PyObject *masko;
	PyArrayObject *permutea, *maska;
	int itype, ne, pt, nm;
	int *permute, *mask;
	npy_intp permute_dims[2];
	int i;

	/*    dbg = fopen ("dbg","w"); */
	Py_Try(PyArg_ParseTuple(args, "Oi", &masko, &itype));
	GET_ARR(maska, masko, PyArray_INT, 1);
	mask = (int *)A_DATA(maska);
	permute_dims[0] = ne = no_edges[itype];
	permute_dims[1] = pt = powers[itype];
	nm = A_DIM(maska, 0);
	if (ne * pt != nm) {
		SETERR("permute and mask must have same number of elements.");
		Py_DECREF(maska);
		return NULL;
	}
	Py_Try(permutea =
	       (PyArrayObject *) PyArray_SimpleNew(2, permute_dims,
						   PyArray_INT));
	permute = (int *)A_DATA(permutea);
	for (i = 0; i < pt; i++, permute++, mask += ne) {
		walk3(permute, mask, itype, pt);
	}
	Py_DECREF(maska);
	/*    fclose (dbg) ; */
	return PyArray_Return(permutea);
}

static char arr_to_corners__doc__[] = "\
This routine takes an array of floats describing cell-centered\n\
values and expands it to node-centered values.";

static PyObject *arr_to_corners(PyObject * self, PyObject * args)
{
	PyObject *oarr, *onv;
	npy_intp sum_nv;
	PyArrayObject *aarr, *anv, *ares;
	int *nv, i, j, snv, jtot;
	double *arr, *res;

	Py_Try(PyArg_ParseTuple(args, "OOi", &oarr, &onv, &sum_nv));
	GET_ARR(aarr, oarr, PyArray_DOUBLE, 1);
	if isARRAY
		(onv) {
		GET_ARR(anv, onv, PyArray_INT, 1);
	} else {
		ERRSS("The second argument must be an Int array");
		Py_DECREF(aarr);
		return (NULL);
	}
	snv = A_SIZE(anv);
	if (snv != A_SIZE(aarr)) {
		ERRSS("The first and second arguments must be the same size.");
		Py_DECREF(aarr);
		Py_DECREF(anv);
		return NULL;
	}
	if (!(ares = (PyArrayObject *)
	      PyArray_SimpleNew(1, &sum_nv, PyArray_DOUBLE))) {
		ERRSS("Unable to create result array.");
		Py_DECREF(aarr);
		Py_DECREF(anv);
		return NULL;
	}
	res = (double *)A_DATA(ares);
	arr = (double *)A_DATA(aarr);
	nv = (int *)A_DATA(anv);
	jtot = 0;
	for (i = 0; i < snv; i++) {
		for (j = 0; j < nv[i]; j++) {
			res[j + jtot] = arr[i];
		}
		jtot = jtot + nv[i];
	}

	Py_DECREF(aarr);
	Py_DECREF(anv);

	return PyArray_Return(ares);
}

/* List of methods defined in the module */

static struct PyMethodDef arr_methods[] = {
	{"array_set", arr_array_set, METH_VARARGS, arr_array_set__doc__},
	{"index_sort", arr_index_sort, METH_VARARGS, arr_index_sort__doc__},
	{"interp", arr_interp, METH_VARARGS, arr_interp__doc__},
	{"zmin_zmax", arr_zmin_zmax, METH_VARARGS, arr_zmin_zmax__doc__},
	{"reverse", arr_reverse, METH_VARARGS, arr_reverse__doc__},
	{"span", arr_span, METH_VARARGS, arr_span__doc__},
	{"nz", arr_nz, METH_VARARGS, arr_nz__doc__},
	{"find_mask", arr_find_mask, METH_VARARGS, arr_find_mask__doc__},
	{"construct3", arr_construct3, METH_VARARGS, arr_construct3__doc__},
	{"to_corners", arr_to_corners, METH_VARARGS, arr_to_corners__doc__},

	{NULL, NULL}		/* sentinel */
};

/* Initialization function for the module (*must* be called initarrayfns) */

static char arrayfns_module_documentation[] = "";

PyMODINIT_FUNC initgistfuncs(void)
{
	PyObject *m, *d;

	/* initialize python */
	Py_Initialize();

	/* initialize numpy */
	import_array();

	/* initialize this module */
	if ((m = Py_InitModule3("gistfuncs", arr_methods,
				arrayfns_module_documentation)) == NULL)
		return;

	/* add symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyErr_NewException("gistfuncs.error", NULL, NULL);
	PyDict_SetItemString(d, "error", ErrorObject);

}
