from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def setup_periodic_tasks(sender: object, **kwargs: object) -> None:
    if sender.__class__.__name__ != "MonitorConfig":
        return
    try:
        from django_celery_beat.models import IntervalSchedule, PeriodicTask

        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )
        PeriodicTask.objects.get_or_create(
            name="Fetch crypto prices every 5 minutes",
            defaults={
                "interval": schedule,
                "task": "monitor.tasks.fetch_prices",
            },
        )
    except Exception:
        pass
