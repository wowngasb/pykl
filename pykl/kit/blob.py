# -*- coding: UTF-8 -*-


from mimetypes import guess_type
from .util import IndexObject


class Blob(IndexObject):

    """A Blob encapsulates a git blob object"""
    DEFAULT_MIME_TYPE = "text/plain"
    type = "blob"

    # valid blob modes
    executable_mode = 0o100755
    file_mode = 0o100644
    link_mode = 0o120000

    __slots__ = ()

    @property
    def mime_type(self):
        """
        :return: String describing the mime type of this file (based on the filename)
        :note: Defaults to 'text/plain' in case the actual file type is unknown. """
        guesses = None
        if self.path:
            guesses = guess_type(self.path)
        return guesses and guesses[0] or self.DEFAULT_MIME_TYPE
