from django.utils import timezone
from datetime import datetime
from django.utils.dateparse import parse_datetime
from freezegun import freeze_time

from crm.models import Customer
from elk.utils.testing import TestCase
from forgot_lessons_search.test.utility.constants import (CUSTOMER_HAS_NOT_OVERDUE_SESSION,
                                                          CUSTOMER_HAS_NOTIFIED_OVERDUE_SESSION,
                                                          CUSTOMER_HAS_OVERDUE_SESSION, FIXTURES_PATH)
from forgot_lessons_search.utility import add_timezone_info, find_customers_with_overdued_sessions, get_list_overdue_session, tuplelist_to_set


@freeze_time('2032-01-01 15:00')
class TestGetForgotLessons(TestCase):
    fixtures = (
        f"{FIXTURES_PATH}/class_model.json",
        f"{FIXTURES_PATH}/customers_model.json",
        f"{FIXTURES_PATH}/entry_model.json",
        f"{FIXTURES_PATH}/lessons_MasterClass_model.json",
        f"{FIXTURES_PATH}/lessons_PairedLesson_model.json",
        f"{FIXTURES_PATH}/teachers_Teacher_model.json",
        f"{FIXTURES_PATH}/user_model.json",
        f"{FIXTURES_PATH}/crm_User_model.json",
        f"{FIXTURES_PATH}/NotificationLog_model.json",
    )

    def setUp(self):
        """
        1. Set customers with different test situations
        """
        self.customer_has_overdue_session = Customer.objects.get(customer_email=CUSTOMER_HAS_OVERDUE_SESSION)
        self.customer_has_not_overdue_session = Customer.objects.get(customer_email=CUSTOMER_HAS_NOT_OVERDUE_SESSION)
        self.customer_has_notified_overdue_session = Customer.objects.get(customer_email=CUSTOMER_HAS_NOTIFIED_OVERDUE_SESSION)

    def test_get_list_overdued_session(self):
        """
        1. Test that customer has overdued session
        2. Test that customer hasn't overdued session
        3. Test that customer hasn't overdued session because it already notified
        """
        self.assertTrue(get_list_overdue_session(self.customer_has_overdue_session))
        self.assertFalse(get_list_overdue_session(self.customer_has_not_overdue_session))
        self.assertFalse(get_list_overdue_session(self.customer_has_notified_overdue_session))

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
        self.assertEqual(len(customers), 1)
        self.assertTrue(self.customer_has_overdue_session.pk in customers)
        self.assertFalse(self.customer_has_not_overdue_session.pk in customers)
        self.assertFalse(self.customer_has_notified_overdue_session.pk in customers)

    def test_tuplelist_to_set(self):
        """
        1. Test that convert list of tuples to set correctly
        """
        listoftuple = [(1,), (2,), (3,), (4,), ]
        setofint = {1, 2, 3, 4, }
        self.assertSetEqual(tuplelist_to_set(listoftuple), setofint)

    def test_add_timezone_info(self):
        """
        1. Test that add time zone info to naive datetime is correct
        """
        self.assertEqual(
            timezone.make_aware(
                parse_datetime('2032-01-01 15:00')),
            add_timezone_info(datetime.now()))
