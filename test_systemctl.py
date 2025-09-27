import subprocess
import getpass
import logging
import os

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_systemctl")

    logger.info(f"Running as user: {getpass.getuser()}")
    logger.info(f"PATH: {os.environ.get('PATH')}")

    # Try reboot with sudo and full path
    try:
        logger.info("Trying: sudo /usr/bin/systemctl reboot --dry-run")
        result = subprocess.run([
            "sudo", "/usr/bin/systemctl", "reboot", "--dry-run"
        ], capture_output=True, text=True, timeout=10)
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"stdout: {result.stdout}")
        logger.info(f"stderr: {result.stderr}")
    except Exception as e:
        logger.error(f"Exception: {e}")

    # Try reboot without sudo
    try:
        logger.info("Trying: /usr/bin/systemctl reboot --dry-run")
        result = subprocess.run([
            "/usr/bin/systemctl", "reboot", "--dry-run"
        ], capture_output=True, text=True, timeout=10)
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"stdout: {result.stdout}")
        logger.info(f"stderr: {result.stderr}")
    except Exception as e:
        logger.error(f"Exception: {e}")

    # Try reboot with sudo and no full path
    try:
        logger.info("Trying: sudo systemctl reboot --dry-run")
        result = subprocess.run([
            "sudo", "systemctl", "reboot", "--dry-run"
        ], capture_output=True, text=True, timeout=10)
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"stdout: {result.stdout}")
        logger.info(f"stderr: {result.stderr}")
    except Exception as e:
        logger.error(f"Exception: {e}")

if __name__ == "__main__":
    main()
