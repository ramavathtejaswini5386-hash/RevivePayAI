from django.db import models


class Transaction(models.Model):

    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('RECOVERED', 'Recovered'),
    ]

    PAYMENT_METHODS = [
        ('UPI', 'UPI'),
        ('CARD', 'Card'),
        ('NETBANKING', 'Net Banking'),
    ]

    transaction_id = models.CharField(max_length=50, unique=True)

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    failure_reason = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    recovery_score = models.IntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"
