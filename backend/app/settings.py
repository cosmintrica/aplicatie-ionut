from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class Settings:
    root_dir: Path = Path(__file__).resolve().parents[2]
    db_path: Path | None = None
    testing: bool = False

    def __post_init__(self):
        self.root_dir = Path(self.root_dir).resolve()
        # app/settings.py -> backend -> project root
        if self.root_dir.name == "backend":
            self.root_dir = self.root_dir.parent
        self.db_path = Path(self.db_path or self.root_dir / "var" / "app.sqlite3").resolve()

    @property
    def allowed_origins(self) -> set[str]:
        origins = {
            f"http://{host}:{port}"
            for host in ("127.0.0.1", "localhost", "[::1]")
            for port in (8000, 5173, 4173)
        }
        if self.testing:
            origins.add("http://testserver")
        return origins

    @property
    def allowed_hosts(self) -> set[str]:
        hosts = {"127.0.0.1", "localhost", "::1"}
        if self.testing:
            hosts.add("testserver")
        return hosts


def default_settings() -> Settings:
    if os.environ.get("APP_MODE", "local") != "local":
        raise RuntimeError("Această versiune acceptă exclusiv APP_MODE=local și acces loopback.")
    return Settings(db_path=Path(os.environ["APP_DB_PATH"]) if "APP_DB_PATH" in os.environ else None)
