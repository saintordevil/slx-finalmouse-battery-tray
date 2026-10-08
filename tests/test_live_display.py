"""SLX-specific display and short-lived animation regressions."""
import threading
import unittest
from unittest import mock

from tests.test_finalmouse_tray import make_app
import finalmouse_tray as tray


class LiveDisplayTests(unittest.TestCase):
    def test_sleep_keeps_last_percentage_without_pulsing_or_finishing_pending_history(self):
        app = make_app({'last_known_pct': 97})
        app._update_icon('97%')
        with mock.patch.object(tray, 'save_charge_log') as save:
            app._update_icon(tray.IDLE_READING)
            self.assertEqual(app._display_key[1], '97%')
            self.assertIn('last read, idle', app.icon.title)
            self.assertEqual(app._pulse_frames, ())
            save.assert_not_called()
        app._update_icon('96%')
        self.assertEqual(app._display_key[1], '96%')
        self.assertNotIn('idle', app.icon.title)

    def test_sleep_before_first_read_does_not_invent_a_percentage(self):
        app = make_app()
        app._update_icon(tray.IDLE_READING)
        self.assertEqual(app._display_key[1], '...')
        self.assertIn('move to read battery', app.icon.title)

    def test_percentage_change_and_repeated_polls_preserve_charge_pulse_phase(self):
        app = make_app()
        app.animate_numbers = True
        with mock.patch.object(tray.time, 'monotonic', return_value=100.0):
            app._update_icon('charging:90%')
        with (mock.patch.object(tray.time, 'monotonic', return_value=100.61),
              mock.patch.object(app.stop_event, 'wait', return_value=False)):
            app._advance_charge_pulse()
            self.assertEqual(app._charge_pulse_phase(), 4)
            app._update_icon('charging:91%')
            app._advance_charge_pulse()
            app._update_icon('charging:91%')
            self.assertEqual(app._pulse_origin, 100.0)
            self.assertEqual(app._charge_pulse_phase(), 4)
            self.assertEqual(app._display_key[1], '91%')
            self.assertEqual(app._display_key[2], (72, 72, 72, 255))

    def test_charge_pulse_is_grey_to_white_and_cache_is_bounded_to_current_number(self):
        app = make_app()
        app.animate_numbers = True
        with mock.patch.object(tray, 'save_charge_log'):
            app._update_icon('charging:55%')
        with mock.patch.object(tray, 'create_battery_icon', wraps=tray.create_battery_icon) as render:
            with mock.patch.object(threading, 'Thread', side_effect=AssertionError('Pulse uses poll loop')):
                for _ in range(36):
                    app._advance_charge_pulse()
        self.assertEqual(render.call_count, len(tray.CHARGE_PULSE_SHADES))
        self.assertEqual(len(app._pulse_frames), 8)
        self.assertEqual(min(tray.CHARGE_PULSE_SHADES), 72)
        self.assertEqual(max(tray.CHARGE_PULSE_SHADES), 255)
        self.assertEqual(app._display_key[1], '55%')
        with mock.patch.object(tray, 'save_charge_log'):
            app._update_icon('56%')
        self.assertEqual(app._pulse_frames, ())
        still = app.icon.icon
        app._advance_charge_pulse()
        self.assertIs(app.icon.icon, still)
        self.assertEqual(app._display_key[2], (255, 255, 255, 255))

    def test_charge_pulse_stops_for_unknown_readings_and_reduced_motion(self):
        app = make_app()
        with mock.patch.object(tray, 'save_charge_log'):
            app._update_icon('charging:55%')
        app.animate_numbers = False
        app._advance_charge_pulse()
        self.assertEqual(app._pulse_frames, ())
        app.animate_numbers = True
        app._update_icon(None)
        app._advance_charge_pulse()
        self.assertEqual(app._pulse_frames, ())
        self.assertEqual(app._display_key[1], '...')

    def test_live_charging_zero_is_real_and_never_replaced_with_previous_charge(self):
        app = make_app({'last_known_pct': 50, 'last_charge': {'start_pct': 30, 'end_pct': 100}})
        with mock.patch.object(tray, 'save_charge_log'):
            app._update_icon('charging:0%')
        self.assertEqual(app.battery_pct, '0%')
        self.assertEqual(app.charge_log['pending_charge']['start_pct'], 0)
        self.assertIn('0% (charging)', app.icon.title)

    def test_white_text_is_kept_despite_an_old_dark_preference(self):
        app = make_app(settings={'dark_text': True})
        app._update_icon('55%')
        pixels = app.icon.icon.getdata()
        self.assertTrue(all((r, g, b) == (255, 255, 255) for r, g, b, a in pixels if a))

    def test_number_transition_uses_bounded_frames_and_no_worker_thread(self):
        app = make_app()
        app.animate_numbers = True
        app._update_icon('55%')
        with mock.patch.object(tray, 'number_transition_frame', wraps=tray.number_transition_frame) as frame:
            with mock.patch.object(threading, 'Thread', side_effect=AssertionError('No animation worker')):
                app._update_icon('56%')
                app._update_icon('56%')
        self.assertEqual(frame.call_count, tray.NUMBER_TRANSITION_FRAMES - 1)
        self.assertEqual(app._display_key[1], '56%')
        self.assertEqual(app.icon.icon.tobytes(), tray.create_battery_icon('56%').tobytes())

    def test_reduced_motion_updates_directly_and_shutdown_cancels_transition(self):
        app = make_app()
        app.animate_numbers = False
        app._update_icon('55%')
        with mock.patch.object(tray, 'number_transition_frame', side_effect=AssertionError('Reduced motion')):
            app._update_icon('56%')
        app.animate_numbers = True
        with mock.patch.object(app.stop_event, 'wait', side_effect=lambda _: app.stop_event.set() or True):
            app._update_icon('57%')
        self.assertTrue(app.stop_event.is_set())
        self.assertNotEqual(app._display_key[1], '57%')

    def test_tooltip_fits_native_limit_and_charge_details_retain_full_history(self):
        app = make_app({'last_charge': {'start_pct': 0, 'end_pct': 100,
                                      'ended_at': '2026-10-08T19:30:00', 'duration_seconds': 43199}})
        with mock.patch.object(tray, 'save_charge_log'):
            app._update_icon('charging:99%')
        self.assertLessEqual(len(app.icon.title), 127)
        self.assertIn('99% (charging)', app.icon.title)
        self.assertTrue(any('0% to 100%' in item.text for item in app._details_menu()))


if __name__ == '__main__':
    unittest.main()
