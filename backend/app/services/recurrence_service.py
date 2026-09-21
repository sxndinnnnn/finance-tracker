"""
Expands a RecurrenceRule into concrete dates. Every fixed transaction, loan
payment, lease payment, and subscription billing cycle goes through this one
function instead of each model re-implementing "what does monthly mean".
"""
from datetime import date

from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY, rrulestr
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

from app.models.recurrence import RecurrenceRule, Frequency

_FREQ_MAP = {
    Frequency.daily: DAILY,
    Frequency.weekly: WEEKLY,
    Frequency.monthly: MONTHLY,
    Frequency.yearly: YEARLY,
}

_WEEKDAY_MAP = {"MO": MO, "TU": TU, "WE": WE, "TH": TH, "FR": FR, "SA": SA, "SU": SU}


def _parse_weekdays(by_weekday: str):
    return [_WEEKDAY_MAP[code.strip().upper()] for code in by_weekday.split(",") if code.strip()]


def _build_rrule(rule: RecurrenceRule):
    if rule.frequency == Frequency.custom and rule.rrule_string:
        return rrulestr(rule.rrule_string, dtstart=rule.start_date)

    kwargs: dict = {"dtstart": rule.start_date, "interval": rule.interval}
    if rule.end_date:
        kwargs["until"] = rule.end_date
    if rule.by_monthday:
        kwargs["bymonthday"] = rule.by_monthday
    if rule.by_weekday:
        kwargs["byweekday"] = _parse_weekdays(rule.by_weekday)
    return rrule(_FREQ_MAP[rule.frequency], **kwargs)


def next_occurrences(rule: RecurrenceRule, after: date, count: int = 1) -> list[date]:
    """Returns the next `count` occurrence dates on/after `after`."""
    occurrences = []
    for occ in _build_rrule(rule):
        occ_date = occ.date()
        if occ_date >= after:
            occurrences.append(occ_date)
        if len(occurrences) >= count:
            break
    return occurrences


def count_occurrences_on_or_before(rule: RecurrenceRule, as_of: date, max_count: int | None = None) -> int:
    """Counts occurrences from the rule's start up to and including `as_of`.

    Used to derive "installments paid so far" for loans/leases from the
    payment schedule itself, instead of a separately maintained counter.
    """
    count = 0
    for occ in _build_rrule(rule):
        if occ.date() > as_of:
            break
        count += 1
        if max_count is not None and count >= max_count:
            break
    return count
