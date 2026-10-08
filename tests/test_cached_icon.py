import unittest
import threading
from unittest import mock

from PIL import Image
from cached_icon import CachedTrayIcon, win32


class CachedIconTests(unittest.TestCase):
    def test_initial_show_and_first_read_are_serialized(self):
        icon = CachedTrayIcon('startup-cache-test', Image.new('RGBA', (32, 32), 'white'))
        self.addCleanup(icon.close_frame_cache)
        showing, release, changed = threading.Event(), threading.Event(), threading.Event()
        def show():
            showing.set()
            if not release.wait(2):
                raise AssertionError('Show was not released')
        def assign():
            icon.icon = Image.new('RGBA', (32, 32), 'gray')
            changed.set()
        with (mock.patch.object(icon, '_show', side_effect=show),
              mock.patch.object(icon, '_update_icon')):
            setup = threading.Thread(target=lambda: setattr(icon, 'visible', True))
            writer = threading.Thread(target=assign)
            try:
                setup.start()
                self.assertTrue(showing.wait(2))
                writer.start()
                self.assertFalse(changed.wait(.05))
            finally:
                release.set()
                setup.join(2)
                if writer.ident is not None:
                    writer.join(2)
                icon._visible = False
        self.assertTrue(changed.is_set())

    def test_icon_assignment_cannot_race_handle_creation(self):
        first = Image.new('RGBA', (32, 32), 'white')
        second = Image.new('RGBA', (32, 32), 'gray')
        icon = CachedTrayIcon('concurrent-cache-test', first)
        self.addCleanup(icon.close_frame_cache)
        loading, release, changed = threading.Event(), threading.Event(), threading.Event()
        original_load = win32.LoadImage
        def load(*args):
            loading.set()
            if not release.wait(2):
                raise AssertionError('Handle load was not released')
            return original_load(*args)
        def change():
            icon.icon = second
            changed.set()
        with mock.patch.object(win32, 'LoadImage', side_effect=load):
            loader = threading.Thread(target=icon._assert_icon_handle)
            writer = threading.Thread(target=change)
            try:
                loader.start()
                self.assertTrue(loading.wait(2))
                writer.start()
                self.assertFalse(changed.wait(.05), 'Image changed during native handle creation')
            finally:
                release.set()
                loader.join(2)
                if writer.ident is not None:
                    writer.join(2)
        self.assertIs(icon._frame_handles[id(first)][0], first)
        self.assertIs(icon.icon, second)

    def test_repeated_frames_reuse_handles_and_cleanup_is_idempotent(self):
        picture = Image.new('RGBA', (32, 32), 'white')
        icon = CachedTrayIcon('cache-test', picture)
        self.addCleanup(icon.close_frame_cache)
        with mock.patch.object(win32, 'LoadImage', wraps=win32.LoadImage) as load:
            icon._assert_icon_handle()
            original = icon._icon_handle
            for _ in range(20):
                icon._release_icon()
                icon._assert_icon_handle()
                self.assertEqual(icon._icon_handle, original)
            self.assertEqual(load.call_count, 1)
        with mock.patch.object(win32, 'DestroyIcon', wraps=win32.DestroyIcon) as destroy:
            icon.close_frame_cache()
            icon.close_frame_cache()
            self.assertEqual(destroy.call_count, 1)

    def test_cache_evicts_old_frames_and_never_exceeds_eight_handles(self):
        icon = CachedTrayIcon('bounded-cache-test', Image.new('RGBA', (32, 32), 'white'))
        self.addCleanup(icon.close_frame_cache)
        with mock.patch.object(win32, 'DestroyIcon', wraps=win32.DestroyIcon) as destroy:
            for shade in range(20):
                icon.icon = Image.new('RGBA', (32, 32), (shade, shade, shade, 255))
                icon._release_icon()
                icon._assert_icon_handle()
                self.assertLessEqual(len(icon._frame_handles), 8)
            self.assertEqual(destroy.call_count, 12)
            icon.close_frame_cache()
            self.assertEqual(destroy.call_count, 20)


if __name__ == '__main__':
    unittest.main()
