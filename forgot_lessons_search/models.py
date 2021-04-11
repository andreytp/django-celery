from django.db import models

class NotificationsLog(models.Model):
    """
    forgot_lessons_search.models.NotificationLog

    Single log of notifications entry 
    =================================
    Single entry of notifications about overdue timelineentry, class, subscription which sent customer 
    Use for checking if the notification was sent early.
    """
    customer = models.ForeignKey("crm.Customer", related_name="log", on_delete=models.CASCADE)

    session = models.ForeignKey('timeline.Entry', related_name="log", on_delete=models.CASCADE, null=True)
    subscription = models.ForeignKey('market.Subscription', related_name="log", on_delete=models.CASCADE, null=True)

    
    customer_email = models.EmailField('Email', blank=True)
    send_date= models.DateTimeField(auto_now_add=True)