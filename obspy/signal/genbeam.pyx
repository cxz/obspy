#!/usr/bin/env python
#-------------------------------------------------------------------
# Filename: genbeam.py
#  Purpose: more general beamforming
#   Author: Joachim Wassermann  
#    Email: j.wassermann@lmu.de
#
# Copyright (C) 2012 J. Wassermann
#---------------------------------------------------------------------
"""
More Generalized beamforming (currently fk and capon supported)

:copyright:
    The ObsPy Development Team (devs@obspy.org)
:license:
    GNU Lesser General Public License, Version 3
    (http://www.gnu.org/copyleft/lesser.html)
"""

import numpy as np
cimport numpy as np
cimport cython


@cython.boundscheck(False)
@cython.wraparound(False)
def generalized_beamformer(np.ndarray[np.float64_t,ndim=2] trace, np.ndarray[np.complex128_t,ndim=4] steer, np.ndarray[np.complex128_t,ndim=4] nsteer, double flow, double fhigh,
         double digfreq, int nsamp, int nstat, int prewhiten, int grdpts_x, int grdpts_y, int nfft, int nf ,np.str method,
         np.ndarray[np.complex128_t, ndim=3] R, np.ndarray[np.complex128_t, ndim=3] R_inv, double dpow):
    """

    """
    # start the code -------------------------------------------------
    # This assumes that all stations and components have the same number of
    # time samples, nt

    cdef int nlow,x,y,i,j,n,ix,iy
    cdef float df
    cdef complex bufi
    cdef complex bufj
    cdef complex xxx
    cdef np.ndarray[np.complex128_t, ndim=1] xx = np.zeros((nfft),dtype=complex)
    cdef np.ndarray[np.float64_t,ndim=3] p = np.zeros((grdpts_x,grdpts_y,nf),dtype=float)
    cdef np.ndarray[np.float64_t,ndim=2] abspow = np.zeros((grdpts_x,grdpts_y),dtype=float)
    cdef np.ndarray[np.float64_t,ndim=2] relpow = np.zeros((grdpts_x,grdpts_y),dtype=float)
    cdef np.ndarray[np.float64_t,ndim=1] white = np.zeros((nf),dtype=float)
    cdef np.ndarray[np.float64_t,ndim=1] tap = np.zeros((nsamp),dtype=float)
    cdef extern from "math.h":
        float sqrt "sqrtf" (float dummy)

    df = digfreq/float(nfft)
    nlow = int(flow/df)

    if method == "bf":
    # P(f) = e.H R(f) e
        for x from 0 <= x < grdpts_x:
            for y from 0 <= y < grdpts_y:
              for n from 0 <= n < nf:
                 bufi = <complex> 0.0
                 for i from 0 <= i < nstat:
                   bufj = <complex> 0.0
                   for j from 0 <= j < nstat:
                      bufj += R[i, j, n] * steer[j, x, y, n]
                   bufi += nsteer[i,x,y,n] * bufj
                 xxx = bufi 
                 if prewhiten == 0:
                    abspow[x,y] += sqrt(xxx.real * xxx.real + xxx.imag*xxx.imag)
                 if prewhiten == 1:
                    p[x,y,n] = sqrt(xxx.real * xxx.real + xxx.imag*xxx.imag)
              if prewhiten == 0:
                 relpow[x,y] = abspow[x,y]/dpow
              if prewhiten == 1:
                 for n from 0 <= n < nf: 
                   if p[x,y,n] > white[n]:
                      white[n] = p[x,y,n]
              
        if prewhiten == 1:
            for x from 0 <= x < grdpts_x:
               for y from 0 <= y < grdpts_y:
                   abspow[x,y] = 0.
                   relpow[x,y] = 0.
                   for n from 0 <= n < nf:
                       abspow[x,y] += p[x,y,n]
                       relpow[x,y] += p[x,y,n]/(white[n]*nf*nstat)

    elif method == "capon":
    # P(f) = 1/(e.H R(f)^-1 e)
        for x from 0 <= x < grdpts_x:
            for y from 0 <= y < grdpts_y:
              for n from 0 <= n < nf:
                  bufi = 0.0
                  for i from 0 <= i < nstat:
                    bufj = 0.0
                    for j from 0 <= j < nstat:
                       bufj += R_inv[i, j, n] * steer[j, x, y, n]
                    bufi += nsteer[i,x,y,n] * bufj
                  xxx = 1. / bufi 
                  if prewhiten == 0:
                      abspow[x,y] += sqrt(xxx.real * xxx.real + xxx.imag*xxx.imag)
                  if prewhiten == 1:
                      p[x,y,n] = sqrt(xxx.real * xxx.real + xxx.imag*xxx.imag)
              if prewhiten == 0:
                 relpow[x,y] = abspow[x,y]
              if prewhiten == 1:
                 for n from 0 <= n < nf:
                   if p[x,y,n] > white[n]:
                      white[n] = p[x,y,n]
        if prewhiten == 1:
            for x from 0 <= x < grdpts_x:
               for y from 0 <= y < grdpts_y:
                  relpow[x,y] = 0.
                  for n from 0 <= n < nf:
                      relpow[x,y] += p[x,y,n]/(white[n]*nf*nstat)

    # find the maximum in the map and return its value and the indices
    ix,iy = np.unravel_index(relpow.argmax(), np.shape(relpow))

    return abspow.max(), relpow.max(), ix, iy

