#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ([2.69])
AC_INIT([opx-tools],[1.0.1],[ops-dev@lists.openswitch.net])
AM_INIT_AUTOMAKE([foreign subdir-objects])
AC_CONFIG_MACRO_DIRS([m4])

# Checks for programs.
AC_PROG_CXX
AM_PATH_PYTHON
AC_PROG_CC
LT_INIT([shared])
# Checks for libraries.

# Checks for typedefs, structures, and compiler characteristics.
AC_CHECK_HEADER_STDBOOL
AC_C_INLINE
AC_TYPE_SIZE_T

# Checks for library functions.
AC_FUNC_MMAP
AC_FUNC_STRERROR_R
AC_CHECK_FUNCS([ftruncate mkdir strncasecmp])

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
