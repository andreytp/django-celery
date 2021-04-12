from datetime import datetime, time

from django.db.models.query_utils import Q
from market.admin import subscriptions

from django.contrib.contenttypes.models import ContentType
from market.models import Subscription

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from crm.models import Customer
from timeline.models import Entry as TimelineEntry

TIMELINE_ENTRY_MODEL_PK = ContentType.objects.get(model='entry').pk
SUBSCRIPTION_MODEL_PK = ContentType.objects.get(model='entry').pk
CUSTOMER_MODEL_PK = ContentType.objects.get(model='entry').pk


def add_timezone_info(date_time: datetime):
    """
    1. Add  timezone information for naive datetimes
    """
    str_date = date_time.strftime('%Y-%m-%d')
    str_time = date_time.strftime('%H:%M')
    return timezone.make_aware(parse_datetime(str_date + ' ' + str_time))


def tuplelist_to_set(values_list: list[tuple[int]], model_pk: int) -> set[tuple[int]]:
    """
    1. Convert list of tuples to set of tuples
    """
    return {*map(lambda x: (x[0], CUSTOMER_MODEL_PK,), values_list)}


def get_list_overdue_session(customer: Customer, **kwargs) -> set[tuple[int]]:
    """
    1. Find overdue session by customer
    2. Exclude sessions that got notifications
    3. Return list of expired sessions pk
    4. Optionally you can set revision_date (by default = now())
    """
    revision_date = datetime.now()
    if kwargs.get('revision_date'):
        revision_date = kwargs.get('revision_date')

    revision_date_max = add_timezone_info(datetime.combine(revision_date, time.max))
    timeline_entries = TimelineEntry \
        .objects \
        .filter(classes__customer__pk=customer.pk) \
        .filter(classes__is_fully_used=False) \
        .filter(log__session__isnull=True) \
        .filter(start__lte=revision_date_max) \
        .filter(classes__is_scheduled=True) \
        .filter(is_finished=False) \
        .values_list('pk')

    return tuplelist_to_set(timeline_entries, TIMELINE_ENTRY_MODEL_PK)


def get_list_overdue_subscription(customer: Customer, **kwargs) -> set[tuple[int]]:
    """
    1. Find overdue session by customer
    2. Exclude sessions that got notifications
    3. Return list of expired sessions pk
    4. Optionally you can set revision_date (by default = now())
    """
    revision_date = datetime.now()
    if kwargs.get('revision_date'):
        revision_date = kwargs.get('revision_date')

    revision_date_max = add_timezone_info(datetime.combine(revision_date, time.max))
    subscriptions_entries = Subscription \
        .objects \
        .filter(customer__pk=customer.pk) \
        .filter(is_fully_used=False) \
        .filter(buy_date__lte=revision_date_max) \
        .filter(log__subscription__isnull=True) \
        .values_list('pk')
    return tuplelist_to_set(subscriptions_entries, SUBSCRIPTION_MODEL_PK)


def find_customers_with_overdued_sessions(**kwargs) -> set[tuple[int]]:
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
        .filter(Q(log__session__isnull=True) & Q(log__subscription__isnull=True)) \
        .filter(classes__is_scheduled=True) \
        .filter(is_finished=False) \
        .values_list('classes__customer__pk')

    return tuplelist_to_set(timeline_entries, CUSTOMER_MODEL_PK)


def find_customers_with_overdued_subscription(**kwargs) -> set[tuple[int]]:
    """
    1. Find all overdue subscriptions
    2. Exclude subscriptions that got notifications
    3. Get distinct customers list from subscriptions
    4. Optionally you can set revision_date (by default = now())
    """
    revision_date = datetime.now()
    if kwargs.get('revision_date'):
        revision_date = kwargs.get('revision_date')

    revision_date_max = add_timezone_info(datetime.combine(revision_date, time.max))

    subscription_entries = subscriptions.Subscription \
        .objects \
        .filter(is_fully_used=False) \
        .filter(buy_date__lte=revision_date_max) \
        .filter(Q(log__session__isnull=True) & Q(log__subscription__isnull=True)) \
        .values_list('customer__pk')

    return tuplelist_to_set(subscription_entries, CUSTOMER_MODEL_PK)


def find_customers_with_overdued_activity(**kwargs) -> set[tuple[int]]:
    """
    Union of sets of customers with overdue session and overdue subscription
    """
    return find_customers_with_overdued_subscription(**kwargs) \
        .union(find_customers_with_overdued_sessions(**kwargs))
