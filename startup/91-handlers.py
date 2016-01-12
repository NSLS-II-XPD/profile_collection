"""
This is a 'hot fix' of an issue that really needs to be fixed in pims.
This is the same as the handler in filestore, AreaDetectorTiffHandler,
except that I cast the slice indices, 'start' and 'stop', to integers.
"""


import pims
import numpy as np
from filestore.handlers import HandlerBase


class FixedAreaDetectorTiffHandler(HandlerBase):
    specs = {'AD_TIFF'} | HandlerBase.specs
    def __init__(self, fpath, template, filename, frame_per_point=1):
        self._path = fpath
        self._fpp = frame_per_point
        self._template = template.replace('_%6.6d', '*')
        self._filename = self._template % (self._path,
                filename)
        self._image_sequence = pims.ImageSequence(self._filename)
    def __call__(self, point_number):
        start = int(point_number * self._fpp)
        stop = int((point_number + 1) * self._fpp)
        if stop > len(self._image_sequence):
            # if asking for an image past the end, make sure we have an up
            # to
            # date list of the existing files
            self._image_sequence = pims.ImageSequence(self._filename)
            if stop > len(self._image_sequence):
                # if we _still_ don't have enough files, raise
                raise IntegrityError("Seeking Frame {0} out of {1} "
                " frames.".format(stop, len(self._image_sequence)))
        return np.asarray(list(self._image_sequence[start:stop])).squeeze()


import databroker  # so that built-in handlers are registered
from filestore.api import deregister_handler, register_handler
deregister_handler('AD_TIFF')
register_handler('AD_TIFF', FixedAreaDetectorTiffHandler)
