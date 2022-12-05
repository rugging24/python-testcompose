from datetime import datetime
from time import sleep
from docker.models.containers import Container
from testcompose.models.container.running_container_attributes import (
    PossibleContainerStates,
    RunningContainerAttributes,
)


class WaitingUtils:
    @staticmethod
    def container_status(container: Container, status="running", delay_ms=2000, timeout_ms=40000) -> bool:
        """Method useful for checking a running container status to
        allow for fetching the latest attribute from the container

        Args:
            status (str, optional): Status to check for. Defaults to "running".
            delay (float, optional): Delay time before the next check. Defaults to 0.1.
            timeout (int, optional): Defaults to 40.
        """
        print(status)
        if status.lower() not in [
            PossibleContainerStates.EXITED.value,
            PossibleContainerStates.RUNNING.value,
        ]:
            raise ValueError("Status must be one of running or exited")

        start: datetime = datetime.now()
        while not (status == (RunningContainerAttributes(**container.attrs)).State.Status):  # type: ignore
            if (datetime.now() - start).total_seconds() * 1000 > timeout_ms:
                print(f"Container status {status} not obtained after {timeout_ms} ms")
                return False
            sleep(delay_ms / 1000)
            container.reload()
        print(f"Found Status {status}")
        return True
