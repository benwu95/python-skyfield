"""Constellation identification.

Constellation identification is tradionally performed with:

http://cdsarc.u-strasbg.fr/viz-bin/Cat?VI/42
https://iopscience.iop.org/article/10.1086/132034/pdf

Given a position, a binary search can be used to index into its roughly
12k data table for a matching declination, but the table then needs to
be scanned linearly for the first subsequent segment that contains the
target right ascension within its bounds.  The big problem for Skyfield:
that algorithm can't be constructed from vectorized NumPy primitives.

So we here take an approach that requires no linear search.  The sky is
divided into a grid, with a grid line at every right ascension and
declination that is mentioned in a constellation boundary.  This is a
bit wasteful, as many values are only ever used for one boundary, but
makes the search easy: do a binary search for right ascension, then for
declination, then look up the indexes in the grid.  Memory requirement:

  1.8k  right ascension table
  1.6k  declination table
 46.6k  grid table
    1k  constellation name abbreviations

"""
from numpy import searchsorted
from .functions import load_bundled_npy
from .timelib import Time, julian_date_of_besselian_epoch

def load_constellation_map():
    """Load Skyfield's constellation map and return a lookup function

    Skyfield carries an internal constellation map that is optimized for
    quick position lookup.  Call this function to load the map and
    return a function mapping position to constellation name.

    >>> from skyfield.api import position_of_radec, load_constellation_map
    >>> constellation_at = load_constellation_map()
    >>> north_pole = position_of_radec(0, 90)
    >>> constellation_at(north_pole)
    'UMi'

    If you pass an array of positions, you'll receive an array of names.

    """
    t1875 = Time(None, julian_date_of_besselian_epoch(1875))

    arrays = load_bundled_npy('constellations.npz')
    sorted_ra = arrays['sorted_ra']
    sorted_dec = arrays['sorted_dec']
    radec_to_index = arrays['radec_to_index']
    indexed_abbreviations = arrays['indexed_abbreviations']

    def constellation_at(position):
        ra, dec, distance = position.radec(epoch=t1875)
        i = searchsorted(sorted_ra, ra.hours)
        j = searchsorted(sorted_dec, dec.degrees, side='right')
        k = radec_to_index[i, j]
        return indexed_abbreviations[k]

    return constellation_at
