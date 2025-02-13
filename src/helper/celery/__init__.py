from time import sleep
from typing import Any, Callable, List

from celery import Celery, chain, chord, group

# تنظیمات Celery
app = Celery(
    "tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)


def simple_task(x: int) -> int:
    return x * x


def retry_task_on_failure(
    task, max_retries: int = 3, countdown: int = 5, *args: Any, **kwargs: Any
) -> Any:
    try:
        return task(*args, **kwargs)
    except Exception as e:
        if task.request.retries < max_retries:
            raise task.retry(exc=e, countdown=countdown)
        else:
            return f"Task failed after {max_retries} retries"


@app.task(bind=True, max_retries=3, default_retry_delay=5)
def long_running_task(self, x: int) -> int:
    try:
        # فرض کنید یه پردازش زمان‌بر دارین
        sleep(10)
        return x * x
    except Exception as e:
        raise self.retry(exc=e)


def chain_tasks(tasks: List[Callable], *args: Any) -> Any:
    task_chain = chain(*tasks)
    return task_chain(*args)


def group_tasks(tasks: List[Callable], *args: Any) -> Any:
    task_group = group(*tasks)
    return task_group(*args)


def chord_tasks(tasks: List[Callable], header_tasks: List[Callable], *args: Any) -> Any:
    task_chord = chord(header_tasks)(group(*tasks))
    return task_chord(*args)


@app.task
def batch_task(data: List[int]) -> List[int]:
    return [x * 2 for x in data]


def async_result_status(task_id: str) -> str:
    result = app.AsyncResult(task_id)
    if result.state == "PENDING":
        return "Task is pending"
    elif result.state == "STARTED":
        return "Task has started"
    elif result.state == "SUCCESS":
        return f"Task succeeded with result: {result.result}"
    elif result.state == "FAILURE":
        return f"Task failed with error: {result.result}"
    else:
        return "Unknown status"


def apply_async_with_custom_retry(task: Callable, *args: Any, **kwargs: Any) -> Any:
    return task.apply_async(args=args, kwargs=kwargs, countdown=10, max_retries=5)


@app.task
def complex_task(x: int, y: int) -> int:
    sleep(2)
    return x + y


@app.task
def task_with_dynamic_args(*args: Any) -> List[Any]:
    return list(args)


def run_concurrent_tasks(tasks: List[Callable], *args: Any) -> List[Any]:
    results = [task.apply_async(args=args) for task in tasks]
    return [result.get() for result in results]


def create_periodic_task(
    schedule: str, task: Callable, *args: Any, **kwargs: Any
) -> None:
    app.conf.beat_schedule[task.name] = {
        "task": task.name,
        "schedule": schedule,
        "args": args,
        "kwargs": kwargs,
    }
    app.conf.timezone = "UTC"


def delay_task(task: Callable, *args: Any, **kwargs: Any) -> Any:
    return task.delay(*args, **kwargs)


def revoke_task(task_id: str) -> bool:
    task_result = app.AsyncResult(task_id)
    if task_result.state == "PENDING":
        task_result.revoke(terminate=True)
        return True
    return False


@app.task
def example_periodic_task():
    return "Periodic task executed!"


def schedule_periodic_task(task: Callable, interval: int) -> None:
    app.conf.beat_schedule[task.name] = {
        "task": task.name,
        "schedule": interval,
    }


def get_task_result(task_id: str) -> Any:
    result = app.AsyncResult(task_id)
    if result.ready():
        return result.result
    return "Task result is not ready yet"


@app.task(bind=True)
def fail_task(self) -> None:
    raise Exception("This task fails")


def check_task_failure(task_id: str) -> bool:
    result = app.AsyncResult(task_id)
    return result.failed()


def chain_with_error_handling(tasks: List[Callable], *args: Any) -> Any:
    try:
        task_chain = chain(*tasks)
        return task_chain(*args)
    except Exception as e:
        return f"Error during task chain execution: {str(e)}"


def delay_with_retry(task: Callable, *args: Any, **kwargs: Any) -> Any:
    return task.apply_async(args=args, kwargs=kwargs, retry=True, max_retries=5)


def group_with_progress(tasks: List[Callable], *args: Any) -> Any:
    task_group = group(*tasks)
    result = task_group.apply_async(args=args)
    return result.get()


def task_with_result_backend(task: Callable, *args: Any, **kwargs: Any) -> Any:
    result = task.apply_async(args=args, kwargs=kwargs)
    return result.get(timeout=10)


@app.task
def task_with_logging(x: int) -> int:
    return x * x
