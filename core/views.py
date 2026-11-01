from django.shortcuts import render, get_object_or_404
from django.db.models import Sum

from .models import Transaction


# ================= HOME =================

def home(request):

    return render(
        request,
        'core/home.html'
    )


# ================= DASHBOARD =================

def dashboard(request):

    transactions = Transaction.objects.all()

    total_transactions = transactions.count()

    # FAILED transactions
    failed_transactions = transactions.filter(
        status='FAILED'
    )

    # Revenue at risk
    revenue_at_risk = failed_transactions.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Recovered revenue
    recovered_revenue = transactions.filter(
        status='RECOVERED'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Recoverable revenue
    recoverable_revenue = transactions.filter(
        status='FAILED',
        recovery_score__gte=70
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Transaction counts
    success_count = transactions.filter(
        status='SUCCESS'
    ).count()

    failed_count = transactions.filter(
        status='FAILED'
    ).count()

    recovered_count = transactions.filter(
        status='RECOVERED'
    ).count()

    # Latest 3 recovered transactions
    recent_recoveries = transactions.filter(
        status='RECOVERED'
    ).order_by(
        '-id'
    )[:3]

    # ================= AI INVESTIGATION ALERT =================

    affected_transactions = failed_transactions.count()

    alert_failure_reason = "No failures"
    alert_payment_method = "No method"

    if affected_transactions > 0:

        latest_failed = failed_transactions.order_by(
            '-created_at'
        ).first()

        if latest_failed.failure_reason:
            alert_failure_reason = latest_failed.failure_reason
        else:
            alert_failure_reason = "UNKNOWN"

        alert_payment_method = latest_failed.payment_method

    # ================= CONTEXT =================

    context = {

        'total_transactions': total_transactions,

        'revenue_at_risk': revenue_at_risk,

        'recoverable_revenue': recoverable_revenue,

        'recovered_revenue': recovered_revenue,

        'success_count': success_count,

        'failed_count': failed_count,

        'recovered_count': recovered_count,

        'recent_recoveries': recent_recoveries,

        # AI Alert
        'affected_transactions': affected_transactions,

        'alert_failure_reason': alert_failure_reason,

        'alert_payment_method': alert_payment_method,
    }

    return render(
        request,
        'core/dashboard.html',
        context
    )


# ================= AI RECOMMENDATION =================

def get_recovery_recommendation(transaction):

    if transaction.status == 'SUCCESS':

        return "Payment completed successfully"

    if transaction.status == 'RECOVERED':

        return "Payment successfully recovered"

    # High-value transaction
    if transaction.amount >= 7000:

        if transaction.recovery_score >= 80:

            return (
                "High-value payment with strong "
                "recovery chance - Retry immediately"
            )

        elif transaction.recovery_score >= 60:

            return (
                "High-value payment - "
                "Retry after a short delay"
            )

        else:

            return (
                "High-value payment with low "
                "recovery chance - Contact customer"
            )

    # Failure reason based recommendation
    if transaction.failure_reason == 'GATEWAY_TIMEOUT':

        return (
            "Temporary gateway issue - "
            "Retry payment after 10 minutes"
        )

    elif transaction.failure_reason == 'BANK_TIMEOUT':

        return (
            "Bank timeout detected - "
            "Retry after 15 minutes"
        )

    elif transaction.failure_reason == 'NETWORK_ERROR':

        return (
            "Network issue detected - "
            "Ask customer to retry"
        )

    # Recovery score based recommendation
    elif transaction.recovery_score >= 80:

        return (
            "High recovery probability - "
            "Retry immediately"
        )

    elif transaction.recovery_score >= 60:

        return (
            "Medium recovery probability - "
            "Send payment reminder"
        )

    else:

        return (
            "Low recovery probability - "
            "Avoid automatic retry"
        )


# ================= AI PRIORITY =================

def get_recovery_priority(transaction):

    if transaction.status != 'FAILED':

        return "NONE"

    if (
        transaction.amount >= 7000
        and transaction.recovery_score >= 70
    ):

        return "HIGH"

    elif transaction.recovery_score >= 60:

        return "MEDIUM"

    else:

        return "LOW"


# ================= TRANSACTIONS =================

def transactions(request):

    transactions = Transaction.objects.all().order_by(
        '-created_at'
    )

    # Get filters from URL
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    search = request.GET.get('search')

    # ================= SEARCH FILTER =================

    if search:

        transactions = transactions.filter(
            transaction_id__icontains=search
        )

    # ================= STATUS FILTER =================

    if status:

        transactions = transactions.filter(
            status=status
        )

    # ================= PRIORITY FILTER =================

    if priority == "HIGH":

        transactions = transactions.filter(
            status='FAILED',
            amount__gte=7000,
            recovery_score__gte=70
        )

    elif priority == "MEDIUM":

        transactions = transactions.filter(
            status='FAILED',
            recovery_score__gte=60
        ).exclude(
            amount__gte=7000,
            recovery_score__gte=70
        )

    elif priority == "LOW":

        transactions = transactions.filter(
            status='FAILED'
        ).filter(
            recovery_score__lt=60
        )

    # ================= ADD AI DATA =================

    for transaction in transactions:

        transaction.recommendation = (
            get_recovery_recommendation(
                transaction
            )
        )

        transaction.priority = (
            get_recovery_priority(
                transaction
            )
        )

    # ================= CONTEXT =================

    context = {

        'transactions': transactions,

        'selected_status': status,

        'selected_priority': priority,

        'search_query': search,

    }

    return render(
        request,
        'core/transactions.html',
        context
    )


# ================= TRANSACTION DETAIL =================

def transaction_detail(request, transaction_id):

    transaction = get_object_or_404(
        Transaction,
        transaction_id=transaction_id
    )

    transaction.recommendation = (
        get_recovery_recommendation(
            transaction
        )
    )

    transaction.priority = (
        get_recovery_priority(
            transaction
        )
    )

    return render(
        request,
        'core/transaction_detail.html',
        {
            'transaction': transaction
        }
    )


# ================= RECOVERY PLAN =================

def recovery_plan(request, transaction_id):

    transaction = get_object_or_404(
        Transaction,
        transaction_id=transaction_id
    )

    recommendation = get_recovery_recommendation(
        transaction
    )

    priority = get_recovery_priority(
        transaction
    )

    context = {

        'transaction': transaction,

        'recommendation': recommendation,

        'priority': priority,
    }

    return render(
        request,
        'core/recovery_plan.html',
        context
    )


# ================= EXECUTE RECOVERY =================

def execute_recovery(request, transaction_id):

    transaction = get_object_or_404(
        Transaction,
        transaction_id=transaction_id
    )

    if request.method == "POST":

        if transaction.status == 'FAILED':

            transaction.status = 'RECOVERED'

            transaction.save()

        return render(
            request,
            'core/recovery_success.html',
            {
                'transaction': transaction
            }
        )

    recommendation = get_recovery_recommendation(
        transaction
    )

    priority = get_recovery_priority(
        transaction
    )

    return render(
        request,
        'core/recovery_plan.html',
        {
            'transaction': transaction,
            'recommendation': recommendation,
            'priority': priority,
        }
    )


# ================= AI INSIGHTS =================

def ai_insights(request):

    transactions = Transaction.objects.all()

    # Total transactions
    total_transactions = transactions.count()

    # ================= STATUS COUNTS =================

    success_count = transactions.filter(
        status='SUCCESS'
    ).count()

    failed_count = transactions.filter(
        status='FAILED'
    ).count()

    recovered_count = transactions.filter(
        status='RECOVERED'
    ).count()

    # ================= FAILED & RECOVERED =================

    failed_transactions = transactions.filter(
        status='FAILED'
    )

    recovered_transactions = transactions.filter(
        status='RECOVERED'
    )

    total_failed = failed_transactions.count()

    total_recovered = recovered_transactions.count()

    # ================= MOST COMMON FAILURE =================

    failure_reasons = {}

    for transaction in failed_transactions:

        reason = transaction.failure_reason or "UNKNOWN"

        if reason in failure_reasons:

            failure_reasons[reason] += 1

        else:

            failure_reasons[reason] = 1

    if failure_reasons:

        most_common_failure = max(
            failure_reasons,
            key=failure_reasons.get
        )

    else:

        most_common_failure = "No failures"

    # ================= RECOVERY SUCCESS RATE =================

    total_attempted_recovery = (
        total_failed +
        total_recovered
    )

    if total_attempted_recovery > 0:

        recovery_success_rate = (
            total_recovered /
            total_attempted_recovery
        ) * 100

    else:

        recovery_success_rate = 0

    # ================= PAYMENT METHOD WITH HIGHEST FAILURE =================

    payment_failures = {}

    for transaction in failed_transactions:

        method = transaction.payment_method or "UNKNOWN"

        if method in payment_failures:

            payment_failures[method] += 1

        else:

            payment_failures[method] = 1

    if payment_failures:

        highest_failure_method = max(
            payment_failures,
            key=payment_failures.get
        )

    else:

        highest_failure_method = "No failures"

    # ================= HIGH PRIORITY COUNT =================

    high_priority_count = 0

    for transaction in failed_transactions:

        if get_recovery_priority(
            transaction
        ) == "HIGH":

            high_priority_count += 1

    # ================= SUCCESS RATE =================

    if total_transactions > 0:

        success_rate = (
            success_count /
            total_transactions
        ) * 100

    else:

        success_rate = 0

    # ================= CHART PERCENTAGES =================

    if total_transactions > 0:

        success_percentage = (
            success_count /
            total_transactions
        ) * 100

        failed_percentage = (
            failed_count /
            total_transactions
        ) * 100

        recovered_percentage = (
            recovered_count /
            total_transactions
        ) * 100

    else:

        success_percentage = 0

        failed_percentage = 0

        recovered_percentage = 0

    # ================= ACTIONABLE RECOMMENDATIONS =================

    recommendations = []

    if total_failed > 0:

        if high_priority_count > 0:

            recommendations.append(
                f"{high_priority_count} high-priority "
                "transaction(s) should be recovered immediately."
            )

        recommendations.append(
            f"Investigate {most_common_failure} failures "
            "to reduce repeated payment issues."
        )

        recommendations.append(
            f"Focus recovery efforts on "
            f"{highest_failure_method} transactions."
        )

        if recovery_success_rate < 50:

            recommendations.append(
                "Recovery success rate is low. Improve retry "
                "strategy and customer notification."
            )

        else:

            recommendations.append(
                "Recovery performance is stable. Continue "
                "monitoring failed transactions."
            )

    else:

        recommendations.append(
            "No failed transactions detected. "
            "Payment system is operating normally."
        )

    # ================= CONTEXT =================

    context = {

        'total_transactions': total_transactions,

        'total_failed': total_failed,

        'total_recovered': total_recovered,

        'most_common_failure': most_common_failure,

        'recovery_success_rate': round(
            recovery_success_rate,
            2
        ),

        'highest_failure_method': highest_failure_method,

        'success_count': success_count,

        'failed_count': failed_count,

        'recovered_count': recovered_count,

        'high_priority_count': high_priority_count,

        'success_rate': round(
            success_rate,
            2
        ),

        # Chart percentages
        'success_percentage': round(
            success_percentage,
            2
        ),

        'failed_percentage': round(
            failed_percentage,
            2
        ),

        'recovered_percentage': round(
            recovered_percentage,
            2
        ),

        # Actionable recommendations
        'recommendations': recommendations,
    }

    return render(
        request,
        'core/ai_insights.html',
        context
    )