import json
from datetime import datetime, timedelta
from unittest import skipIf
from unittest.mock import patch
import sys
import os

from django.contrib.auth.models import User
from django.core import serializers
from freezegun import freeze_time

import lessons.models as lessons
import products
import teachers.models as teachers
from crm.models import Customer
from crm.models import User as crm_user
from elk.utils.testing import TestCase, create_customer, create_teacher
from forgot_lessons_search.models import NotificationsLog as Notifications
from forgot_lessons_search.utility import add_timezone_info
from market.models import Class, Subscription
from market.sortinghat import SortingHat
from timeline.models import Entry as TimelineEntry

from .constants import (CUSTOMER_HAS_NOT_OVERDUE_SESSION, CUSTOMER_HAS_NOTIFIED_OVERDUE_SESSION,
                        CUSTOMER_HAS_NOTIFIED_OVERDUE_SUBSCRIPTION, CUSTOMER_HAS_OVERDUE_SESSION,
                        CUSTOMER_HAS_OVERDUE_SUBSCRIPTION, FIXTURES_PATH)

TEST_PRODUCT_ID = 1
LESSON_ID = 500

GENERATOR_NAME = "'forgot_lessons_search.test.utility.fixtures_generator'"


@skipIf(GENERATOR_NAME not in sys.argv[2], "Only use when change test cases")
@freeze_time('2032-01-01 15:00')
class TestFixtureGenerator(TestCase):
    """
    Generate data for test casess and save it as fixtures
    """
    fixtures = ('lessons', 'products', )

    def setUp(self):
        """
        1. Buy a 4 lessons for customer, schedule it every week from 3 weeks ago to one week forward
        2. Set first sheduled session as finished
        3. Set second sheduled lesson as unfinished
        4. Buy a three lessons for other customer, schedule it every week forward from this moment.
        5. Buy a 4 lessons for third customer, schedule it every week from 3 weeks ago to one week forward
        6. Set first sheduled session as unfinished
        7. Set up notification log record for this session
        8. Set second sheduled lesson as unfinished
        9. Set up notification log record for this session
        10. Set up overdued subscription that lessons aren't scheduled
        """
        product = products.models.Product1.objects.get(pk=TEST_PRODUCT_ID)
        teacher = create_teacher(accepts_all_lessons=True, works_24x7=True)
        lesson = lessons.MasterClass.objects.get(pk=LESSON_ID)
        lesson.host = teacher
        lesson.save()

        self.customer_has_overdue_subscription = create_customer(customer_email=CUSTOMER_HAS_OVERDUE_SUBSCRIPTION)
        self.customer_has_overdue_session = create_customer(customer_email=CUSTOMER_HAS_OVERDUE_SESSION)
        self.customer_has_not_overdue_session = create_customer(customer_email=CUSTOMER_HAS_NOT_OVERDUE_SESSION)
        self.customer_has_notified_overdue_session = create_customer(customer_email=CUSTOMER_HAS_NOTIFIED_OVERDUE_SESSION)
        self.customer_has_notified_overdue_subscription = create_customer(customer_email=CUSTOMER_HAS_NOTIFIED_OVERDUE_SUBSCRIPTION)

        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta=-21, is_finished=True)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta=-14, is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta=-7, is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_overdue_session, lesson, days_delta=7, is_finished=False)

        teacher1 = create_teacher(accepts_all_lessons=True, works_24x7=True)
        lesson1 = lessons.PairedLesson.objects.get(pk=LESSON_ID)
        lesson1.host = teacher1
        lesson1.save()

        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta=7, is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta=14, is_finished=False)
        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson1, days_delta=21, is_finished=False)

        teacher2 = create_teacher(accepts_all_lessons=True, works_24x7=True)
        lesson2 = lessons.LessonWithNative.objects.get(pk=LESSON_ID)
        lesson2.host = teacher2
        lesson2.save()

        self._setup_sheduled_lesson(self.customer_has_not_overdue_session, lesson2, days_delta=-21, is_finished=True)

        first_overdue_timeline_entry = self._setup_sheduled_lesson(self.customer_has_notified_overdue_session, lesson2, days_delta=-14, is_finished=False)
        self._make_notification_session(self.customer_has_notified_overdue_session, first_overdue_timeline_entry, add_timezone_info(datetime.now() + timedelta(days=-7)))

        second_overdue_timeline_entry = self._setup_sheduled_lesson(self.customer_has_notified_overdue_session, lesson2, days_delta=-7, is_finished=False)
        self._make_notification_session(self.customer_has_notified_overdue_session, second_overdue_timeline_entry, add_timezone_info(datetime.now()))

        self._setup_sheduled_lesson(self.customer_has_notified_overdue_session, lesson2, days_delta=7, is_finished=False)

        with freeze_time('2031-12-25 15:00'):
            self.subscription = Subscription(
                customer=self.customer_has_overdue_subscription,
                product=product,
                buy_price=150,
            )
            self.subscription.save()

            self.subscription_with_notification = Subscription(
                customer=self.customer_has_notified_overdue_subscription,
                product=product,
                buy_price=150,
            )
            self.subscription_with_notification.save()
        self._make_notification_subscription(self.customer_has_notified_overdue_subscription, self.subscription_with_notification, add_timezone_info(datetime.now()))

        self._dump_models_data()

    def testTrue(self):
        """
        Fake test to run setUp()
        """
        self.assertTrue(True)

    def _dump_models_data(self):
        """
        Save models data to fixtures
        """

        with open(FIXTURES_PATH + "user_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", User.objects.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "customers_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", Customer.objects.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "class_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", Class.objects.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "entry_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", TimelineEntry.objects.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "lessons_MasterClass_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", lessons.MasterClass.objects.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "lessons_PairedLesson_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", lessons.PairedLesson.objects.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "teachers_Teacher_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", teachers.Teacher.objects.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "crm_User_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", crm_user.objects.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "subscriptionClasses_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", self.subscription.classes.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "subscription_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", Subscription.objects.all())), f, indent=4, sort_keys=True)

        with open(FIXTURES_PATH + "NotificationLog_model.json", "w") as f:
            json.dump(json.loads(serializers.serialize("json", Notifications.objects.all())), f, indent=4, sort_keys=True)

    def _make_notification_session(self, customer: Customer, entry: TimelineEntry, date_send: datetime) -> Notifications:
        """
        Make notification log record for timeline entry
        """
        notification = Notifications(
            customer=customer,
            session=entry,
            customer_email=customer.customer_email,
            send_date=date_send,
        )
        notification.save()
        return notification

    def _make_notification_subscription(self, customer: Customer, entry: Subscription, date_send: datetime) -> Notifications:
        """
        Make notification log record for market subscriptions
        """
        notification = Notifications(
            customer=customer,
            subscription=entry,
            customer_email=customer.customer_email,
            send_date=date_send,
        )
        notification.save()
        return notification

    def _setup_sheduled_lesson(self, customer: User, lesson: lessons.Lesson, days_delta: int = 0, is_finished: bool = False):
        """
        Buy lesson for customer, create timeline entry and shedule class
        """
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
        Make timeline entry record about lesson
        """
        entry = TimelineEntry(
            slots=1,
            lesson=lesson,
            teacher=lesson.host,
            start=start_time,
            is_finished=is_finished,
        )

        return entry

    def _buy_a_lesson(self, lesson_customer: Customer, lesson: lessons.Lesson):
        """
        Got a lesson for customer
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
