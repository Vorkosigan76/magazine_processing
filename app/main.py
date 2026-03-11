import logging
import os
import sys
import time
from pathlib import Path

from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from app.processor import load_magazines, process_file
from app.version import BUILD_DATE, BUILD_TIME, VERSION

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

IMPORT_DIR = Path(os.environ.get("IMPORT_DIR", "/import"))
PROCESSED_DIR = Path(os.environ.get("PROCESSED_DIR", "/processed"))
QUARANTINE_DIR = Path(os.environ.get("QUARANTINE_DIR", "/quarantine"))


class MagazineHandler(FileSystemEventHandler):
    def __init__(self, magazines: list[dict], output_dir: Path, quarantine_dir: Path):
        self.magazines = magazines
        self.output_dir = output_dir
        self.quarantine_dir = quarantine_dir

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return
        filepath = Path(event.src_path)
        if filepath.suffix.lower() != ".pdf":
            return
        # Brief delay to let the file finish being written/copied
        time.sleep(1)
        process_file(filepath, self.magazines, self.output_dir, self.quarantine_dir)
        # Remove the parent folder if it's now empty (and not the import root)
        parent = filepath.parent
        if parent != IMPORT_DIR:
            try:
                parent.rmdir()
                logger.info("Removed empty folder: %s", parent)
            except OSError:
                pass


def process_existing(import_dir: Path, magazines: list[dict], output_dir: Path, quarantine_dir: Path):
    """Process any PDFs already sitting in the import directory (including subfolders)."""
    for f in import_dir.rglob("*"):
        if f.is_file() and f.suffix.lower() == ".pdf":
            process_file(f, magazines, output_dir, quarantine_dir)
    cleanup_empty_dirs(import_dir)


def cleanup_empty_dirs(import_dir: Path):
    """Remove empty subdirectories inside the import directory (bottom-up)."""
    for dirpath in sorted(import_dir.rglob("*"), reverse=True):
        if dirpath.is_dir():
            try:
                dirpath.rmdir()  # only succeeds if empty
                logger.info("Removed empty folder: %s", dirpath)
            except OSError:
                pass


def main():
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Magazine Processor v%s (built %s %s)", VERSION, BUILD_DATE, BUILD_TIME)

    magazines = load_magazines()
    logger.info("Loaded %d magazine pattern(s)", len(magazines))

    logger.info("Starting periodic check (every 10 minutes)")

    try:
        while True:
            try:
                logger.info("Checking %s for new PDFs...", IMPORT_DIR)
                process_existing(IMPORT_DIR, magazines, PROCESSED_DIR, QUARANTINE_DIR)
                logger.info("Check complete. Next check in 10 minutes.")
            except Exception as e:
                logger.error("Error during check: %s", e, exc_info=True)
                logger.info("Continuing despite error. Next check in 10 minutes.")
            time.sleep(600)  # 10 minutes
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()
