from datetime import datetime
import re
from time import sleep
from typing import Optional, Match
from docker.models.containers import Container
from testcompose.models.config.container_log_wait_parameters import LogWaitParameter


class LogWaiter:
    @staticmethod
    def search_container_logs(test_container: Container, log_parameter: LogWaitParameter) -> None:
        """Search for a given predicate in the container log. Useful to check if a
        container is running and healthy

        Args:
            search_string (str): predicate to search in the log
            timeout (float, optional): Defaults to 300.0.
            interval (int, optional): Defaults to 1.

        Raises:
            ValueError: if a non string predicate is passed

        Returns:
            bool: True if the log contains the provided predicate
        """
        if not log_parameter:
            return

        if not isinstance(log_parameter.log_line_regex, str):
            raise ValueError

        prog = re.compile(log_parameter.log_line_regex, re.MULTILINE).search
        start = datetime.now()
        output: Optional[Match[str]] = None
        while (datetime.now() - start).total_seconds() < (log_parameter.wait_timeout_ms / 1000):
            output = prog(test_container.logs().decode())
            if output:
                return
            if (datetime.now() - start).total_seconds() > (log_parameter.wait_timeout_ms / 1000):
                raise TimeoutError(
                    "container %s did not emit logs satisfying predicate in %.3f seconds"
                    % (test_container.name, float(log_parameter.wait_timeout_ms or 60000))
                )
            sleep(log_parameter.poll_interval_ms / 1000)
        print("%s", test_container.logs().decode())
        return
