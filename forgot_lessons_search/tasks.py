from datetime import datetime

from crm.models import Customer
from elk.celery import app as celery
from forgot_lessons_search.models import NotificationsLog as Notifications
from forgot_lessons_search.signals import customers_with_overdue_sessions_signal
from forgot_lessons_search.utility import (SUBSCRIPTION_MODEL_PK, TIMELINE_ENTRY_MODEL_PK, add_timezone_info,
                                           find_customers_with_overdued_activity, get_list_overdue_session,
                                           get_list_overdue_subscription)
from market.models import Subscription
from timeline.models import Entry as TimelineEntry


@celery.task
def notify_overdue_session():
    """
    Get set of customers that have either overdue session(class) or overdue subscription
    Send email notification to this customers
    Store in notification log that notification was sent to this customers
    """
    notified_customers = set()
    customers_tuples = find_customers_with_overdued_activity()
    for customer_tuple in customers_tuples:
        customer_instance = Customer.objects.get(pk=customer_tuple[0])

        if customer_instance not in notified_customers:  # to avoid dublication of customer notification
            customers_with_overdue_sessions_signal.send(sender=notify_overdue_session, instance=customer_instance)
            notified_customers.add(customer_instance)

        if customer_tuple[1] == TIMELINE_ENTRY_MODEL_PK:
            for session_tuple in get_list_overdue_session(customer_instance):
                session_instance = TimelineEntry.objects.get(pk=session_tuple[0])

                notify_log_entry = Notifications(
                    customer=customer_instance,
                    session=session_instance,
                    customer_email=customer_instance.email,
                    send_date=add_timezone_info(datetime.now())
                )
                notify_log_entry.save()

        if customer_tuple[1] == SUBSCRIPTION_MODEL_PK:
            for subscription_tuple in get_list_overdue_subscription(customer_instance):
                subscription_instance = Subscription.objects.get(pk=subscription_tuple[0])

                notify_log_entry = Notifications(
                    customer=customer_instance,
                    subscription=subscription_instance,
                    customer_email=customer_instance.email,
                    send_date=add_timezone_info(datetime.now())
                )
                notify_log_entry.save()
