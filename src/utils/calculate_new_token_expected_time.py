from datetime import timedelta
from zoneinfo import ZoneInfo


NEPAL_TIMEZONE = ZoneInfo("Asia/Kathmandu")

# If there is no actual execution data yet,
# use the original 3-minute prediction.
DEFAULT_EXECUTION_SECONDS = 180

# If there is no actual waiting data yet,
# assume no additional waiting.
DEFAULT_WAITING_SECONDS = 0


def calculate_new_token_expected_time(tokens):
    """
    Calculate expected_time for a newly created token
    when token service has already started.

    `tokens` should contain the existing tokens for the
    same department and date.

    The new token is assumed to be placed after all
    existing waiting tokens.
    """

    if not tokens:
        return None

    # ---------------------------------------------------------
    # Sort tokens in queue order
    # ---------------------------------------------------------

    tokens = sorted(
        tokens,
        key=lambda token: token.id
    )

    # ---------------------------------------------------------
    # Calculate average execution duration
    # from tokens that have actually completed.
    # ---------------------------------------------------------

    execution_values = [
        token.execution_duration
        for token in tokens
        if token.execution_duration is not None
        and token.execution_duration >= 0
    ]

    if execution_values:

        average_execution = (
            sum(execution_values)
            / len(execution_values)
        )

    else:

        average_execution = DEFAULT_EXECUTION_SECONDS

    # ---------------------------------------------------------
    # Calculate average waiting time
    # from tokens that have actually started.
    # ---------------------------------------------------------

    waiting_values = [
        token.waiting_time
        for token in tokens
        if token.waiting_time is not None
        and token.waiting_time >= 0
    ]

    if waiting_values:

        average_waiting = (
            sum(waiting_values)
            / len(waiting_values)
        )

    else:

        average_waiting = DEFAULT_WAITING_SECONDS

    # ---------------------------------------------------------
    # Find the currently serving token
    # ---------------------------------------------------------

    serving_tokens = [
        token
        for token in tokens
        if token.token_status == "serving"
        and token.started_at is not None
    ]

    serving_tokens.sort(
        key=lambda token: token.id
    )

    # ---------------------------------------------------------
    # If a token is currently serving,
    # start prediction from its estimated end.
    # ---------------------------------------------------------

    if serving_tokens:

        serving_token = serving_tokens[-1]

        if serving_token.execution_duration is not None:

            current_time = (
                serving_token.started_at
                + timedelta(
                    seconds=serving_token.execution_duration
                )
            )

        else:

            current_time = (
                serving_token.started_at
                + timedelta(
                    seconds=average_execution
                )
            )

    else:

        # -----------------------------------------------------
        # Otherwise find the latest completed token.
        # -----------------------------------------------------

        completed_tokens = [
            token
            for token in tokens
            if token.token_status == "completed"
            and token.ended_at is not None
        ]

        completed_tokens.sort(
            key=lambda token: token.id
        )

        if not completed_tokens:
            return None

        last_completed_token = completed_tokens[-1]

        current_time = last_completed_token.ended_at

    # ---------------------------------------------------------
    # Get all existing waiting tokens.
    #
    # These tokens are ahead of the newly created token.
    # ---------------------------------------------------------

    waiting_tokens = [
        token
        for token in tokens
        if token.token_status == "waiting"
        and token.deleted_by_department is None
    ]

    waiting_tokens.sort(
        key=lambda token: token.id
    )

    # ---------------------------------------------------------
    # Move through all existing waiting tokens.
    #
    # For each waiting token:
    #
    #     previous service
    #          +
    #     average waiting
    #          =
    #     expected start
    #
    # Then add average execution time to estimate
    # when that token will finish.
    # ---------------------------------------------------------

    for waiting_token in waiting_tokens:

        # Waiting before this token starts
        current_time = (
            current_time
            + timedelta(
                seconds=average_waiting
            )
        )

        # Service time for this token
        current_time = (
            current_time
            + timedelta(
                seconds=average_execution
            )
        )

    # ---------------------------------------------------------
    # Now calculate the expected time of the NEW token.
    #
    # It is after all existing waiting tokens.
    # ---------------------------------------------------------

    expected_datetime = (
        current_time
        + timedelta(
            seconds=average_waiting
        )
    )

    # ---------------------------------------------------------
    # Convert UTC datetime to Nepal time.
    # ---------------------------------------------------------

    expected_time = (
        expected_datetime
        .astimezone(NEPAL_TIMEZONE)
        .time()
        .replace(microsecond=0)
    )

    return expected_time