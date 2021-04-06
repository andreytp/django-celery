from crm.models import Customer
from market.models import Class as Session
from timeline.models import Entry as TimelineEntry
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.utils.dateparse import parse_datetime

def add_timezone_info(date_time: datetime):
    str_date = date_time.strftime('%Y-%m-%d')
    str_time = date_time.strftime('%H:%M')
    return timezone.make_aware(parse_datetime(str_date + ' ' + str_time))

def has_overdue_session(customer: Customer, **kwargs)-> bool:
    """
    1. Find overdue session by customer
    2. Return True if it is
    3. Optionally you can set revision_date (by default = now())
    """
    revision_date = datetime.now()
    if kwargs.get('revision_date'):
        revision_date = kwargs.get('revision_date')

    revision_date += timedelta(days=-7)
    revision_date_max = add_timezone_info(datetime.combine(revision_date, time.max))

    timeline_entries = TimelineEntry \
    .objects \
    .filter(classes__customer__pk=customer.pk) \
    .filter(start__lt= revision_date_max) \
    .filter(classes__is_scheduled=True) \
    .filter(is_finished=False)

    return timeline_entries

def find_customers_with_overdued_sessions(**kwargs)->list[str]:
    """
    1. Find all overdue sessions
    2. Get distinct customers list from sessions
    3. Optionally you can set revision_date (by default = now())
    """
    revision_date = datetime.now()
    if kwargs.get('revision_date'):
        revision_date = kwargs.get('revision_date')

    revision_date_max = add_timezone_info(datetime.combine(revision_date, time.max))

    timeline_entries = TimelineEntry \
    .objects \
    .filter(start__lt= revision_date_max) \
    .filter(classes__is_scheduled=True) \
    .filter(is_finished=False) \
    .values_list('classes__customer__pk')

    return list(*set(timeline_entries))
