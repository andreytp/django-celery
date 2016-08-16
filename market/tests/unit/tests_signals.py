from datetime import datetime
from unittest.mock import MagicMock

from django.test import TestCase
from django.utils import timezone
from mixer.backend.django import mixer

from elk.utils.testing import create_customer, create_teacher
from lessons import models as lessons
from market import signals
from market.models import Class
from teachers.models import WorkingHours


class TestClassSignals(TestCase):
    fixtures = ('lessons',)

    def setUp(self):
        self.customer = create_customer()
        self.teacher = create_teacher()
        self.lesson = lessons.OrdinaryLesson.get_default()
        mixer.blend(WorkingHours, teacher=self.teacher, weekday=0, start='13:00', end='15:00')  # monday

    def _buy_a_lesson(self):
        c = Class(
            customer=self.customer,
            lesson=self.lesson
        )
        c.save()
        return c

    def _schedule(self, c, date=datetime(2032, 12, 1, 11, 30)):  # By default it will fail in 16 years, sorry
        if timezone.is_naive(date):
            date = timezone.make_aware(date)

        c.schedule(
            teacher=self.teacher,
            date=date,
            allow_besides_working_hours=True,
        )
        c.save()
        self.assertTrue(c.is_scheduled)
        return c

    def _test_scheduled_class_signal(self):
        handler = MagicMock()
        c = self._buy_a_lesson()
        signals.class_scheduled.connect(handler)
        self._schedule(c)
        self.assertEqual(handler.call_count, 1)
        return [c, handler]

    def test_scheduled_class_signal_called_once(self):
        [c, handler] = self._test_scheduled_class_signal()
        c.save()  # signal is emited during the save() method, so let's call it one more time
        self.assertEqual(handler.call_count, 1)

    def _test_unscheduled_class_signal(self):
        handler = MagicMock()
        c = self._buy_a_lesson()
        signals.class_unscheduled.connect(handler)
        self._schedule(c)
        c.unschedule()
        self.assertEqual(handler.call_count, 0)  # assert that signal is not emited during the unschedule, because it can fail
        c.save()
        self.assertEqual(handler.call_count, 1)
        return [c, handler]

    def test_unscheduled_class_signal_called_once(self):
        [c, handler] = self._test_unscheduled_class_signal()
        c.save()  # signal is emited during the save() method, so let's call it one more time
        self.assertEqual(handler.call_count, 1)