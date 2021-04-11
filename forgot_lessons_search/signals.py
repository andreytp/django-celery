from django.dispatch import Signal, receiver

from mailer.owl import Owl

customers_with_overdue_sessions_signal = Signal(providing_args=['instance'])


@receiver(customers_with_overdue_sessions_signal, dispatch_uid='notify_customers_overdue_session')
def notify_customers_overdue_session(sender, **kwargs):
    """
    Send email notification to customers
    """
    customer = kwargs['instance']
    owl = Owl(
        template='mail/overdue.html',
        ctx={
            'customer': customer,
        },
        to=[customer.user.email],
        timezone=customer.timezone,
    )
    owl.send()
