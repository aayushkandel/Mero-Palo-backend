from datetime import datetime, timedelta, time


def calculate_expected_time(
    token_start: time,
    token_number: int
):
    expected_datetime = datetime.combine(
        datetime.today(),
        token_start
    ) + timedelta(
        minutes=3 * (token_number - 1)
    )

    return expected_datetime.time()