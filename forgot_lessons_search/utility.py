from datetime import datetime, time, timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from crm.models import Customer
from timeline.models import Entry as TimelineEntry


def add_timezone_info(date_time: datetime):
    """
    1. Add  timezone information for naive datetimes
    """
    str_date = date_time.strftime('%Y-%m-%d')
    str_time = date_time.strftime('%H:%M')
    return timezone.make_aware(parse_datetime(str_date + ' ' + str_time))


def tuplelist_to_set(values_list: list[tuple]) -> set[int]:
    """
    1. Convert list of tuples to set
    """
    return {*map(lambda x: x[0], values_list)}


def get_list_overdue_session(customer: Customer, **kwargs) -> set[int]:
    """
    1. Find overdue session by customer
    2. Exclude sessions that got notifications
    3. Return list of expired sessions pk
    4. Optionally you can set revision_date (by default = now())
    """
    revision_date = datetime.now()
    if kwargs.get('revision_date'):
        revision_date = kwargs.get('revision_date')

    revision_date += timedelta(days=-7)
    revision_date_max = add_timezone_info(datetime.combine(revision_date, time.max))

    timeline_entries = TimelineEntry \
        .objects \
        .filter(classes__customer__pk=customer.pk) \
        .filter(log__session__isnull=True) \
        .filter(start__lt=revision_date_max) \
        .filter(classes__is_scheduled=True) \
        .filter(is_finished=False) \
        .values_list('pk')

    return tuplelist_to_set(timeline_entries)

def find_customers_with_overdued_sessions(**kwargs) -> set[int]:
    """
    1. Find all overdue sessions
    2. Exclude sessions that got notifications
    3. Get distinct customers list from sessions
    4. Optionally you can set revision_date (by default = now())
    """
    revision_date = datetime.now()
    if kwargs.get('revision_date'):
        revision_date = kwargs.get('revision_date')

    revision_date_max = add_timezone_info(datetime.combine(revision_date, time.max))

    timeline_entries = TimelineEntry \
        .objects \
        .filter(start__lt=revision_date_max) \
        .filter(log__session__isnull=True) \
        .filter(classes__is_scheduled=True) \
        .filter(is_finished=False) \
        .values_list('classes__customer__pk')

    return tuplelist_to_set(timeline_entries)
