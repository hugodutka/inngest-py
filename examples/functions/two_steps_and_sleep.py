import datetime

import inngest


@inngest.create_function(
    inngest.FunctionOpts(id="two_steps_and_sleep", name="Two steps and sleep"),
    inngest.TriggerEvent(event="app/two_steps_and_sleep"),
)
def fn(*, step: inngest.Step, **_kwargs: object) -> str:
    user_id = step.run("get_user_id", lambda: 1)
    step.run("print_user_id", lambda: f"user ID is {user_id}")

    step.sleep_until(
        "zzzzz",
        (datetime.datetime.now() + datetime.timedelta(seconds=3)),
    )

    return "done"