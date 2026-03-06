import logging
import os
import sys
import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from app.processor import load_magazines, process_file

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


def process_existing(import_dir: Path, magazines: list[dict], output_dir: Path, quarantine_dir: Path):
    """Process any PDFs already sitting in the import directory."""
    for pdf in import_dir.glob("*.pdf"):
        process_file(pdf, magazines, output_dir, quarantine_dir)


def main():
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    magazines = load_magazines()
    logger.info("Loaded %d magazine pattern(s)", len(magazines))

    # Process files that already exist before we start watching
    process_existing(IMPORT_DIR, magazines, PROCESSED_DIR, QUARANTINE_DIR)

    handler = MagazineHandler(magazines, PROCESSED_DIR, QUARANTINE_DIR)
    observer = Observer()
    observer.schedule(handler, str(IMPORT_DIR), recursive=False)
    observer.start()
    logger.info("Watching %s for new PDFs...", IMPORT_DIR)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
