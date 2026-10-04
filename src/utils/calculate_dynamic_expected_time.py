from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo


NEPAL_TIMEZONE = ZoneInfo("Asia/Kathmandu")

DEFAULT_EXECUTION_SECONDS = 180
DEFAULT_WAITING_SECONDS = 0


def calculate_dynamic_expected_times(
    tokens
):
    """
    Recalculate expected_time for all waiting tokens.

    Completed tokens:
        Use their actual execution_duration.

    Waiting time:
        Use actual waiting_time where available.

    Future tokens:
        Use average execution duration and average waiting time.
    """

    if not tokens:
        return

    # ---------------------------------------------------------
    # Calculate average execution duration
    # ---------------------------------------------------------

    execution_values = [
        token.execution_duration
        for token in tokens
        if token.execution_duration is not None
        and token.execution_duration >= 0
    ]

    if execution_values:
        average_execution = sum(execution_values) / len(execution_values)
    else:
        average_execution = DEFAULT_EXECUTION_SECONDS

    # ---------------------------------------------------------
    # Calculate average waiting time
    # ---------------------------------------------------------

    waiting_values = [
        token.waiting_time
        for token in tokens
        if token.waiting_time is not None
        and token.waiting_time >= 0
    ]

    if waiting_values:
        average_waiting = sum(waiting_values) / len(waiting_values)
    else:
        average_waiting = DEFAULT_WAITING_SECONDS

    # ---------------------------------------------------------
    # Find the last token which has actually finished
    # ---------------------------------------------------------

    completed_tokens = [
        token
        for token in tokens
        if token.token_status == "completed"
        and token.ended_at is not None
    ]

    completed_tokens.sort(key=lambda token: token.id)

    # ---------------------------------------------------------
    # Find the last completed token's end time
    # ---------------------------------------------------------

    if completed_tokens:
        last_completed_token = completed_tokens[-1]

        current_time = last_completed_token.ended_at

    else:
        # If nothing has completed yet, find a started token.
        started_tokens = [
            token
            for token in tokens
            if token.started_at is not None
        ]

        started_tokens.sort(key=lambda token: token.id)

        if started_tokens:
            current_time = started_tokens[-1].started_at
        else:
            return

    # ---------------------------------------------------------
    # Update remaining waiting tokens
    # ---------------------------------------------------------

    waiting_tokens = [
        token
        for token in tokens
        if token.token_status == "waiting"
        and token.deleted_by_department is None
    ]

    waiting_tokens.sort(key=lambda token: token.id)

    for token in waiting_tokens:

        # -----------------------------------------------------
        # Expected start of this token
        #
        # First add average waiting time.
        # -----------------------------------------------------

        predicted_start = (
            current_time
            + timedelta(seconds=average_waiting)
        )

        token.expected_time = predicted_start.astimezone(
            NEPAL_TIMEZONE
        ).time().replace(microsecond=0)

        # -----------------------------------------------------
        # After this token starts, we predict its execution
        # duration before calculating the next token.
        # -----------------------------------------------------

        current_time = (
            predicted_start
            + timedelta(seconds=average_execution)
        )