"""
Expands a RecurrenceRule into concrete dates. Every fixed transaction, loan
payment, lease payment, and subscription billing cycle goes through this one
function instead of each model re-implementing "what does monthly mean".
"""
from datetime import date

from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY, rrulestr

from app.models.recurrence import RecurrenceRule, Frequency

_FREQ_MAP = {
    Frequency.daily: DAILY,
    Frequency.weekly: WEEKLY,
    Frequency.monthly: MONTHLY,
    Frequency.yearly: YEARLY,
}


def next_occurrences(rule: RecurrenceRule, after: date, count: int = 1) -> list[date]:
    """Returns the next `count` occurrence dates on/after `after`."""
    if rule.frequency == Frequency.custom and rule.rrule_string:
        rr = rrulestr(rule.rrule_string, dtstart=rule.start_date)
    else:
        kwargs: dict = {"dtstart": rule.start_date, "interval": rule.interval}
        if rule.end_date:
            kwargs["until"] = rule.end_date
        if rule.by_monthday:
            kwargs["bymonthday"] = rule.by_monthday
        rr = rrule(_FREQ_MAP[rule.frequency], **kwargs)

    occurrences = []
    for occ in rr:
        occ_date = occ.date()
        if occ_date >= after:
            occurrences.append(occ_date)
        if len(occurrences) >= count:
            break
    return occurrences
