from datetime import datetime, timedelta
from re import U
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import serializers
from freezegun import freeze_time
from mixer.backend.django import mixer

import lessons.models as lessons
import teachers.models as teachers
from crm.models import Customer
from crm.models import User as crm_user
from elk.utils.testing import TestCase
from elk.utils.testing import create_customer, create_teacher
from forgot_lessons_search.utility import add_timezone_info
from forgot_lessons_search.models import NotificationsLog
from market.models import Class
from market.sortinghat import SortingHat
from timeline.models import Entry as TimelineEntry
from .constants import CUSTOMER_HAS_OVERDUE_SESSION, FIXTURES_PATH
from .constants import CUSTOMER_HAS_NOT_OVERDUE_SESSION
from .constants import CUSTOMER_HAS_NOTIFIED_OVERDUE_SESSION

@freeze_time('2032-01-01 15:00')
class TestFuxtureGenerator(TestCase):
    
    def setUp(self):
        """
        Former TestClass setUp method
        1. Buy a 4 lessons for customer, schedule it every week from 3 weeks ago to one week forward
        2. Set first sheduled session as finished
        3. Set second sheduled lesson as unfinished
        4. Buy a three lessons for other customer, schedule it every week forward from this moment.
        5. Buy a 4 lessons for third customer, schedule it every week from 3 weeks ago to one week forward
        6. Set first sheduled session as unfinished
        7. Set up notification log record for this session
        8. Set second sheduled lesson as unfinished
        9. Set up notification log record for this session
        """
        self.customer_has_overdue_session = create_customer(customer_email=CUSTOMER_HAS_OVERDUE_SESSION)
        teacher = create_teacher(accepts_all_lessons=True, works_24x7=True)
        lesson = mixer.blend('lessons.MasterClass', host=teacher, slots=1)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta= -21, is_finished=True)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta= -14, is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta= -7,  is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta=  7,  is_finished=False)

        self.customer_has_not_overdue_session = create_customer(customer_email=CUSTOMER_HAS_NOT_OVERDUE_SESSION)
        teacher1 = create_teacher(accepts_all_lessons=True, works_24x7=True)
        lesson1 = mixer.blend('lessons.PairedLesson', host=teacher1, slots=1)
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta= 7, is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta= 14,  is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta=  21,  is_finished=False)

        self.customer_has_notified_overdue_session = create_customer(customer_email=CUSTOMER_HAS_NOTIFIED_OVERDUE_SESSION)
        teacher1 = create_teacher(accepts_all_lessons=True, works_24x7=True)
        lesson1 = mixer.blend('lessons.PairedLesson', host=teacher1, slots=1)
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta= -21, is_finished=True)

        first_overdue_timeline_entry = self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta= -14,  is_finished=False)
        self._make_notification(self.customer_has_notified_overdue_session, first_overdue_timeline_entry)

        second_overdue_timeline_entry = self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta=  -7,  is_finished=False)
        self._make_notification(self.customer_has_notified_overdue_session, second_overdue_timeline_entry)
        
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta=   7,  is_finished=False)

        self._dump_models_data()


    def testTrue(self):
        self.assertTrue(True)

    def _make_notification(self, customer: Customer, timeline_entry: TimelineEntry)->NotificationsLog:
        notification = NotificationsLog(
            customer=customer,
            session=timeline_entry,
            customer_email=customer.customer_email,
            send_date=timeline_entry.start+timedelta(days=7),
        )
        notification.save()
        return notification
    
    def _dump_models_data(self):
        path_to_fixtures = FIXTURES_PATH

        with open(path_to_fixtures + "user_model.json", "w") as f:
            f.write(serializers.serialize("json", User.objects.all()))
       
        with open(path_to_fixtures + "customers_model.json", "w") as f:
            f.write(serializers.serialize("json", Customer.objects.all()))

        with open(path_to_fixtures + "class_model.json", "w") as f:
            f.write(serializers.serialize("json", Class.objects.all()))

        with open(path_to_fixtures + "entry_model.json", "w") as f:
            f.write(serializers.serialize("json", TimelineEntry.objects.all()))

        with open(path_to_fixtures + "lessons_MasterClass_model.json", "w") as f:
            f.write(serializers.serialize("json", lessons.MasterClass.objects.all()))
        
        with open(path_to_fixtures + "lessons_PairedLesson_model.json", "w") as f:
            f.write(serializers.serialize("json", lessons.PairedLesson.objects.all()))

        with open(path_to_fixtures + "teachers_Teacher_model.json", "w") as f:
            f.write(serializers.serialize("json", teachers.Teacher.objects.all()))
        
        with open(path_to_fixtures + "crm_User_model.json", "w") as f:
            f.write(serializers.serialize("json", crm_user.objects.all()))
        
        with open(path_to_fixtures + "NotificationLog_model.json", "w") as f:
            f.write(serializers.serialize("json", NotificationsLog.objects.all()))


        
    def _setup_sheduled_lesson(self, customer: User, lesson: lessons.Lesson, days_delta: int = 0, is_finished: bool = False):
        now_datetime = add_timezone_info(datetime.now())
        session_date = now_datetime + timedelta(days=days_delta)
        session = self._buy_a_lesson(customer, lesson)
        entry = self._create_entry(session_date, lesson, is_finished)
        entry.save()
        self._schedule(session, entry, lesson)
        return entry
        
 
    @patch('timeline.models.Entry.clean')
    def _create_entry(self, start_time: datetime, lesson: lessons.Lesson, is_finished: bool, clean):
        """
        Make entry record about lesson 
        """
        entry = TimelineEntry(
            slots=1,
            lesson=lesson,
            teacher=lesson.host,
            start=start_time,
            is_finished = is_finished,
        )
        
        return entry

    def _buy_a_lesson(self, lesson_customer: Customer, lesson: lessons.Lesson):
        """
        Got a lesson
        """
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
