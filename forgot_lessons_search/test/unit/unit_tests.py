from datetime import datetime

from django.test.testcases import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from freezegun import freeze_time

from crm.models import Customer
from forgot_lessons_search.test.utility.constants import (CUSTOMER_HAS_NOT_OVERDUE_SESSION,
                                                          CUSTOMER_HAS_NOTIFIED_OVERDUE_SESSION,
                                                          CUSTOMER_HAS_NOTIFIED_OVERDUE_SUBSCRIPTION,
                                                          CUSTOMER_HAS_OVERDUE_SESSION,
                                                          CUSTOMER_HAS_OVERDUE_SUBSCRIPTION, FIXTURES_PATH)
from forgot_lessons_search.utility import (CUSTOMER_MODEL_PK, add_timezone_info, find_customers_with_overdued_activity,
                                           find_customers_with_overdued_sessions,
                                           find_customers_with_overdued_subscription, get_list_overdue_session,
                                           get_list_overdue_subscription, tuplelist_to_set)


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
        f"{FIXTURES_PATH}/subscription_model.json",
        f"{FIXTURES_PATH}/NotificationLog_model.json",
    )

    def setUp(self):
        """
        1. Set customers with different test situations
        """
        self.customer_has_overdue_session = Customer.objects.get(customer_email=CUSTOMER_HAS_OVERDUE_SESSION)
        self.customer_has_not_overdue_session = Customer.objects.get(customer_email=CUSTOMER_HAS_NOT_OVERDUE_SESSION)
        self.customer_has_notified_overdue_session = Customer.objects.get(customer_email=CUSTOMER_HAS_NOTIFIED_OVERDUE_SESSION)
        self.customer_has_overdue_subscription = Customer.objects.get(customer_email=CUSTOMER_HAS_OVERDUE_SUBSCRIPTION)
        self.customer_has_notified_overdue_subscription = Customer.objects.get(customer_email=CUSTOMER_HAS_NOTIFIED_OVERDUE_SUBSCRIPTION)

    def test_get_list_overdued_session(self):
        """
        Get list overdue session(class) for particular customer
        1. Test that customer has overdued session
        2. Test that customer hasn't overdued session
        3. Test that customer hasn't overdued session because it already notified
        """
        self.assertTrue(get_list_overdue_session(self.customer_has_overdue_session))
        self.assertFalse(get_list_overdue_session(self.customer_has_not_overdue_session))
        self.assertFalse(get_list_overdue_session(self.customer_has_notified_overdue_session))

    def test_get_list_overdued_subscription(self):
        """
        Test get list overdue subscription for particular customer
        1. Test that customer has overdued subscription
        2. Test that customer hasn't overdued subscription
        3. Test that customer hasn't overdued subscription because it already notified
        """
        self.assertTrue(get_list_overdue_subscription(self.customer_has_overdue_subscription))
        self.assertFalse(get_list_overdue_subscription(self.customer_has_notified_overdue_subscription))

    def test_there_is_customer_with_overdued_sessions(self):
        """
        Test find customer that has overdued session(class)
        1. Get non empty list of customers that has overdued sessions.
        2. Test that list not empty
        3. Test that list size is correct
        4. Test that list item is correct
        5. Test that list does not contain incorrect values
        """
        customers = find_customers_with_overdued_sessions()
        self.assertTrue(len(customers))
        self.assertEqual(len(customers), 1)
        self.assertTrue((self.customer_has_overdue_session.pk, CUSTOMER_MODEL_PK,) in customers)
        self.assertFalse((self.customer_has_not_overdue_session.pk, CUSTOMER_MODEL_PK,) in customers)
        self.assertFalse((self.customer_has_notified_overdue_session.pk, CUSTOMER_MODEL_PK,) in customers)

    def test_find_overdue_subscription_customer(self):
        """
        Test find customer that has overdued subscription
        1. Get non empty list of customers that has subscription that has not sheduled lessons and subscription buy date was 7 days ago
        2. Test that list not empty
        3. Test that list size is correct
        4. Test that list item is correct
        5. Test that list does not contain incorrect values
        """
        customers = find_customers_with_overdued_subscription()
        self.assertTrue(len(customers))
        self.assertEqual(len(customers), 1)
        self.assertTrue((self.customer_has_overdue_subscription.pk, CUSTOMER_MODEL_PK,) in customers)
        self.assertFalse((self.customer_has_notified_overdue_subscription.pk, CUSTOMER_MODEL_PK,) in customers)

    def test_find_overdue_activities_customer(self):
        """
        Test find customer that has overdued subscription or session(class)
        1. Get non empty list of customers that has subscription that has not sheduled lessons and subscription buy date was 7 days ago
        2. Test that list not empty
        3. Test that list size is correct
        4. Test that list item is correct
        5. Test that list does not contain incorrect values
        """
        customers = find_customers_with_overdued_activity()
        self.assertTrue(len(customers))
        self.assertEqual(len(customers), 2)
        self.assertTrue((self.customer_has_overdue_subscription.pk, CUSTOMER_MODEL_PK,) in customers)
        self.assertFalse((self.customer_has_notified_overdue_subscription.pk, CUSTOMER_MODEL_PK,) in customers)
        self.assertTrue((self.customer_has_overdue_session.pk, CUSTOMER_MODEL_PK,) in customers)
        self.assertFalse((self.customer_has_not_overdue_session.pk, CUSTOMER_MODEL_PK,) in customers)
        self.assertFalse((self.customer_has_notified_overdue_session.pk, CUSTOMER_MODEL_PK,) in customers)

    def test_tuplelist_to_set(self):
        """
        Test that convert list of tuples to set correctly
        """
        listoftuple = [(1,), (2,), (3,), (4,), ]
        setoftuple = {(1, CUSTOMER_MODEL_PK,), (2, CUSTOMER_MODEL_PK,), (3, CUSTOMER_MODEL_PK,), (4, CUSTOMER_MODEL_PK,), }
        self.assertSetEqual(tuplelist_to_set(listoftuple, CUSTOMER_MODEL_PK), setoftuple)

    def test_add_timezone_info(self):
        """
        Test that add time zone info to naive datetime is correct
        """
        self.assertEqual(
            timezone.make_aware(
                parse_datetime('2032-01-01 15:00')),
            add_timezone_info(datetime.now()))
