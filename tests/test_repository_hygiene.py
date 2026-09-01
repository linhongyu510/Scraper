import subprocess
from pathlib import Path


def scan_tracked_text_files(root: Path, forbidden: tuple[str, ...]) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    offenders: list[str] = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(raw_path.decode())
        if relative.parts[:2] == ("docs", "superpowers"):
            continue
        try:
            content = (root / relative).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(value in content for value in forbidden):
            offenders.append(str(relative))
    return offenders


def test_tracked_text_files_do_not_contain_session_credentials() -> None:
    forbidden = (
        "SESS" + "DATA=",
        "bili_" + "jct=",
        "Dede" + "UserID=",
        "Cookie" + '":',
    )

    assert scan_tracked_text_files(Path.cwd(), forbidden) == []
