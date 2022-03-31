class RhelContainerException(Exception):
    """RheContainer custom exception."""

    def __init__(self, msg, stdout=None, stderr=None, command=None):
        self.msg = msg
        self.stdout = stdout
        self.stderr = stderr
        self.command = command

    @classmethod
    def from_subprocess_out(cls, msg, sub_out):
        stdout = sub_out.stdout.decode().strip() if sub_out.stdout else ""
        stderr = sub_out.stderr.decode().strip() if sub_out.stderr else ""
        command = " ".join(sub_out.args)
        return cls(
            msg=msg,
            stdout=stdout,
            stderr=stderr,
            command=command,
        )

    def __str__(self):
        return f"{self.msg}: \n{self.command} -> \n{self.stderr}  \n{self.stdout}"
