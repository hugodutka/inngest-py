import inngest
import tests.helper

# TODO: Remove when middleware is ready for external use.
from inngest._internal import execution, middleware_lib, types

from . import base

_TEST_NAME = "function_middleware"


class _State(base.BaseState):
    def __init__(self) -> None:
        self.hook_list: list[str] = []


def create(
    framework: str,
    is_sync: bool,
) -> base.Case:
    test_name = base.create_test_name(_TEST_NAME, is_sync)
    event_name = base.create_event_name(framework, test_name, is_sync)
    state = _State()

    class _MiddlewareSync(middleware_lib.MiddlewareSync):
        def after_execution(self) -> None:
            state.hook_list.append("after_execution")

        def before_response(self) -> None:
            # This hook is not called for function middleware but we'll include
            # in anyway to verify that.
            state.hook_list.append("before_response")

        def before_execution(self) -> None:
            state.hook_list.append("before_execution")

        def transform_input(
            self,
            call_input: execution.TransformableCallInput,
        ) -> execution.TransformableCallInput:
            state.hook_list.append("transform_input")
            return call_input

        def transform_output(
            self,
            output: inngest.Serializable,
        ) -> inngest.Serializable:
            state.hook_list.append("transform_output")
            return output

    class _MiddlewareAsync(middleware_lib.Middleware):
        async def after_execution(self) -> None:
            state.hook_list.append("after_execution")

        async def before_response(self) -> None:
            # This hook is not called for function middleware but we'll include
            # in anyway to verify that.
            state.hook_list.append("before_response")

        async def before_execution(self) -> None:
            state.hook_list.append("before_execution")

        async def transform_input(
            self,
            call_input: execution.TransformableCallInput,
        ) -> execution.TransformableCallInput:
            state.hook_list.append("transform_input")
            return call_input

        async def transform_output(
            self,
            output: inngest.Serializable,
        ) -> inngest.Serializable:
            state.hook_list.append("transform_output")
            return output

    @inngest.create_function(
        fn_id=test_name,
        middleware=[_MiddlewareSync],
        retries=0,
        trigger=inngest.TriggerEvent(event=event_name),
    )
    def fn_sync(
        *,
        logger: types.Logger,
        step: inngest.StepSync,
        run_id: str,
        **_kwargs: object,
    ) -> None:
        logger.info("function start")
        state.run_id = run_id

        def _first_step() -> None:
            logger.info("first_step")

        step.run("first_step", _first_step)

        logger.info("between steps")

        def _second_step() -> None:
            logger.info("second_step")

        step.run("second_step", _second_step)
        logger.info("function end")

    @inngest.create_function(
        fn_id=test_name,
        middleware=[_MiddlewareAsync],
        retries=0,
        trigger=inngest.TriggerEvent(event=event_name),
    )
    async def fn_async(
        *,
        logger: types.Logger,
        step: inngest.Step,
        run_id: str,
        **_kwargs: object,
    ) -> None:
        logger.info("function start")
        state.run_id = run_id

        def _first_step() -> None:
            logger.info("first_step")

        await step.run("first_step", _first_step)

        logger.info("between steps")

        def _second_step() -> None:
            logger.info("second_step")

        await step.run("second_step", _second_step)
        logger.info("function end")

    def run_test(self: base.TestClass) -> None:
        self.client.send_sync(inngest.Event(name=event_name))
        run_id = state.wait_for_run_id()
        tests.helper.client.wait_for_run_status(
            run_id,
            tests.helper.RunStatus.COMPLETED,
        )

        # Assert that the middleware hooks were called in the correct order
        assert state.hook_list == [
            # Entry 1
            "transform_input",
            "before_execution",
            "after_execution",
            "transform_output",
            # Entry 2
            "transform_input",
            "before_execution",
            "after_execution",
            "transform_output",
            # Entry 3
            "transform_input",
            "before_execution",
            "after_execution",
            "transform_output",
        ], state.hook_list

    if is_sync:
        fn = fn_sync
    else:
        fn = fn_async

    return base.Case(
        event_name=event_name,
        fn=fn,
        run_test=run_test,
        state=state,
        name=test_name,
    )