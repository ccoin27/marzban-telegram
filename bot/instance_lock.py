import os
import sys
from pathlib import Path

_fd: int | None = None


def acquire(project_root: Path) -> None:
    global _fd
    if sys.platform == "win32":
        return
    import fcntl

    path = project_root / ".bot.lock"
    _fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(_fd)
        _fd = None
        print(
            "Уже запущен другой экземпляр бота с этим проектом.\n"
            "Если используете systemd: не запускайте start.sh / python main.py вручную.\n"
            "Остановите лишний процесс: sudo systemctl stop marzban-telegram.service или pkill -f main.py",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        os.ftruncate(_fd, 0)
        os.write(_fd, str(os.getpid()).encode("ascii"))
    except OSError:
        pass
