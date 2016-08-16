from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'check_classes_that_will_start_soon': {
        'task': 'market.tasks.notify_15min_to_class',
        'schedule': timedelta(minutes=1),
    },
    'mark_classes_as_fully_used': {
        'task': 'market.tasks.mark_classes_as_fully_used',
        'schedule': timedelta(minutes=3),
    }
}