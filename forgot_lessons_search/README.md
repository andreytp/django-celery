There are several approaches to solving the problem of notifying clients about overdue classes:
    
    1. It is possible to check expired classes that were expired a week ago at every startup
        The advantage - there is no need to store any data, easy to realize the task
        Disadvantage - if you disrupt the launch schedule, you may miss the notification or disguise it
    
    2. It is possible to store dates and time when task was started
        Benefits -  a minimum of stored information, it is not difficult to implement the task
        Disadvantage - need to store launch data info, wrong functioning is possible after changing lesson or subscription dates 
    
    3. It is possible to store every notification in the database
        Benefits - every notification send one time, every moment it is information about when notification was sent
        Disadvantages - need to store notification information in the database

As the most reliable I have chosen to implement the third approach

In development, I restricted code changes outside of my application, so sometimes I had to apply suboptimal solutions
So to register lesson notifications and subscription notifications two different fields are used
You could have used GenericForeignKey instead, but you would have had to change the timeline.Entry and market.Subscription models, which was undesirable

When I was researching this project I made database scheme which available at django-celery.drawio file in this folder 
which can be opened with hediet.vscode-drawio VSCode extension or on https://draw.io