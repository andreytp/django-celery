import csv
from unittest.mock import patch
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import pytz

from freezegun import freeze_time
from mixer.backend.django import mixer

from elk.utils.testing import TestCase, create_customer, create_teacher
from timeline.models import Entry as TimelineEntry
from forgot_lessons_search.utility import add_timezone_info
from forgot_lessons_search.utility import has_overdue_session
from forgot_lessons_search.utility import find_customers_with_overdued_sessions
from market.models import Class
from market.sortinghat import SortingHat


@freeze_time('2032-01-01 15:00')
class TestGetForgotLessons(TestCase):
    
    def setUp(self):
        """
        1. Buy a 4 lessons for customer, schedule it every week from 3 weeks ago to one week forward
        2. Set first sheduled session as finished
        3. Set second sheduled lesson as unfinished
        4. Buy a three lessons for other customer, schedule it every week forward from this moment
        """
        self.customer_has_overdue_session = create_customer()
        teacher = create_teacher(accepts_all_lessons=True, works_24x7=True)
        lesson = mixer.blend('lessons.MasterClass', host=teacher, slots=1)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta= -21, is_finished=True)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta= -14, is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta= -7,  is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta=  7,  is_finished=False)

        self.customer_has_not_overdue_session = create_customer()
        teacher1 = create_teacher(accepts_all_lessons=True, works_24x7=True)
        lesson1 = mixer.blend('lessons.PairedLesson', host=teacher1, slots=1)
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta= 7, is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta= 14,  is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta=  21,  is_finished=False)

    def test_customer_has_overdued_session(self):
        """
        1. Test that customer has overdued session
        2. Test that customer hasn't overdued session
        """
        self.assertTrue(has_overdue_session(self.customer_has_overdue_session))
        self.assertFalse(has_overdue_session(self.customer_has_not_overdue_session))

    def test_there_is_customer_with_overdued_sessions(self):
        """
        1. Get non empty list of customers that has overdued sessions.
        2. Test that list not empty
        3. Test that list size is correct
        4. Test that list item is correct
        5. Test that list does not contain incorrect values
        """    
        customers = find_customers_with_overdued_sessions()
        self.assertTrue(customers)
        self.assertEqual(len(customers),1)
        self .assertEqual(customers[0], self.customer_has_overdue_session.pk)
        self.assertFalse(self.customer_has_not_overdue_session.pk in customers)
        
    def _setup_sheduled_lesson(self, customer: 'auth.user', lesson: 'lesson', days_delta: int = 0, is_finished: bool = False):
        now_datetime = add_timezone_info(datetime.now())
        session_date = now_datetime + timedelta(days=days_delta)
        session = self._buy_a_lesson(customer, lesson)
        entry = self._create_entry(session_date, lesson)
        entry.save()
        self._schedule(session, entry, lesson)
        entry.is_finished = is_finished
        entry.save()
 
    @patch('timeline.models.Entry.clean')
    def _create_entry(self, start_time: datetime, lesson, clean ):
        entry = TimelineEntry(
            slots=1,
            lesson=lesson,
            teacher=lesson.host,
            start=start_time,
        )
        self.assertFalse(entry.is_finished)
        return entry

    def _buy_a_lesson(self, lesson_customer, lesson):
        session = Class(
            customer=lesson_customer,
            lesson_type=lesson.get_contenttype(),
        )
        session.save()
        self.assertFalse(session.is_fully_used)
        self.assertFalse(session.is_scheduled)
        return session

    @patch('timeline.models.Entry.clean')
    def _schedule(self, session, entry, lesson, clean):
        """
        Schedule a class to given timeline entry.

        ACHTUNG: for class with non-hosted lessons the entry will be the new one,
        not the one you've supplied.
        """
        clean.return_value = True
        hat = SortingHat(
            customer=session.customer,
            lesson_type=lesson.get_contenttype().pk,
            teacher=entry.teacher,
            date=entry.start.strftime('%Y-%m-%d'),
            time=entry.start.strftime('%H:%M'),
        )
        if not hat.do_the_thing():
            self.assertFalse(True, "Cant schedule a lesson: %s" % hat.err)
        self.assertEqual(hat.c, session)
        hat.c.save()

        session.refresh_from_db()
