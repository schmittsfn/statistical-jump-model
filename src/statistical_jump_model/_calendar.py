from functools import lru_cache
import exchange_calendars as xcals

@lru_cache
def calendar(end_year):
    return xcals.get_calendar("XNYS", start="1926-01-01", end=f"{end_year+1}-12-31")
