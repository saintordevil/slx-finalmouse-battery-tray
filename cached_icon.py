"""Bounded Windows icon-handle reuse for pystray's repeating pulse frames."""
from collections import OrderedDict
import threading

import pystray
from pystray._util import win32


class CachedTrayIcon(pystray.Icon):
    """Keep at most eight HICONs; release all after the tray window closes.

    pystray otherwise serializes an ICO file and reloads it on every frame.
    The cache owns its image references, so Python id reuse cannot alias a frame.
    """

    MAX_HANDLES = 8

    def __init__(self, *args, **kwargs):
        self._frame_handles = OrderedDict()
        self._frame_lock = threading.RLock()
        super().__init__(*args, **kwargs)

    @property
    def icon(self):
        with self._frame_lock:
            return pystray.Icon.icon.fget(self)

    @icon.setter
    def icon(self, value):
        # Serialize the image assignment itself, not only _update_icon. The
        # setup thread can otherwise load the placeholder while polling swaps
        # in the first reading, then incorrectly mark the placeholder current.
        with self._frame_lock:
            pystray.Icon.icon.fset(self, value)

    @property
    def visible(self):
        with self._frame_lock:
            return pystray.Icon.visible.fget(self)

    @visible.setter
    def visible(self, value):
        with self._frame_lock:
            pystray.Icon.visible.fset(self, value)

    def _assert_icon_handle(self):
        with self._frame_lock:
            if self._icon_handle:
                return
            key = id(self.icon)
            cached = self._frame_handles.get(key)
            if cached is not None:
                self._icon_handle = cached[1]
                self._frame_handles.move_to_end(key)
                return
            super()._assert_icon_handle()
            self._frame_handles[key] = (self.icon, self._icon_handle)
            while len(self._frame_handles) > self.MAX_HANDLES:
                _, (_, handle) = self._frame_handles.popitem(last=False)
                win32.DestroyIcon(handle)

    def _release_icon(self):
        # Borrowed from the cache. Eviction or close_frame_cache owns destruction.
        with self._frame_lock:
            self._icon_handle = None

    def _update_icon(self):
        with self._frame_lock:
            super()._update_icon()

    def _show(self):
        with self._frame_lock:
            super()._show()

    def close_frame_cache(self):
        with self._frame_lock:
            self._icon_handle = None
            for _, handle in self._frame_handles.values():
                win32.DestroyIcon(handle)
            self._frame_handles.clear()

    def __del__(self):
        try:
            super().__del__()
        finally:
            self.close_frame_cache()
