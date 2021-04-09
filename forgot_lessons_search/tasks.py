from crm.models import Customer
from elk.celery import app as celery
from forgot_lessons_search.signals import customers_with_overdue_sessions_signal
from forgot_lessons_search.utility import find_customers_with_overdued_sessions
from forgot_lessons_search.utility import get_list_overdue_session
from forgot_lessons_search.utility import add_timezone_info
from forgot_lessons_search.models import NotificationsLog
from datetime import datetime
from timeline.models import Entry as TimelineEntry


@celery.task
def notify_overdue_session():
    
    customers_pk = find_customers_with_overdued_sessions()
    for customer_pk in customers_pk:
        customer_instance = Customer.objects.get(pk=customer_pk)
        customers_with_overdue_sessions_signal.send(sender=notify_overdue_session, instance=customer_instance)
        for session_pk in get_list_overdue_session(customer_instance):
            session_instance = TimelineEntry.objects.get(pk=session_pk)
                
            notify_log_entry = NotificationsLog(
                customer=customer_instance,
                session=session_instance,
                customer_email=customer_instance.email,
                send_date=add_timezone_info(datetime.now())
            )
            notify_log_entry.save()
