from unittest.mock import patch
from time import sleep

from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from freezegun import freeze_time

from crm.models import Customer
from forgot_lessons_search.models import NotificationsLog
from forgot_lessons_search.tasks import notify_overdue_session
from forgot_lessons_search.test.utility.constants import (CUSTOMER_HAS_NOT_OVERDUE_SESSION,
                                                          CUSTOMER_HAS_NOTIFIED_OVERDUE_SESSION,
                                                          CUSTOMER_HAS_OVERDUE_SESSION, FIXTURES_PATH)
from forgot_lessons_search.utility import get_list_overdue_session
from mailer.owl import Owl


@override_settings(
    EMAIL_HOST='smtp.mailtrap.io',
    EMAIL_HOST_USER='501c4e07d71747',
    EMAIL_HOST_PASSWORD='451bec655fa869',
    EMAIL_PORT='2525',
)
class TestNotifyOverdueEmail(TestCase):
    fixtures =(
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
        self.customer_with_overdue_session = Customer.objects.get(customer_email=CUSTOMER_HAS_OVERDUE_SESSION)


    @patch('market.signals.Owl')
    def test_ovedue_notification(self, Owl:Owl):
        with freeze_time('2032-01-01 15:00'):
            for _ in range(10):  # run this 10 times to check for repietive emails — all notifications should be sent one time
                notify_overdue_session()

        self.assertEqual(len(mail.outbox), 1) 
        out_emails = [outbox.to[0] for outbox in mail.outbox]

        self.assertIn(self.customer_with_overdue_session.email, out_emails)

    @override_settings(EMAIL_ASYNC=True, CELERY_ALWAYS_EAGER=True, CELERY_ACCEPT_CONTENT = ['pickle'],)   
    def test_send_email(self):
        with freeze_time('2032-01-01 15:00'):
            notify_overdue_session()
            self.assertTrue(NotificationsLog.objects.all())
            self.assertFalse(get_list_overdue_session(self.customer_with_overdue_session))

