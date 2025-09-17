#!/usr/bin/env python
"""
Celery worker management for testing.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def start_worker():
    """Start Celery worker in the background."""
    env = os.environ.copy()
    env.update({
        "CELERY_BROKER_URL": "amqp://admin:admin@localhost:5672//",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/1",
        "PYTHONPATH": str(project_root / "src"),
    })

    cmd = [
        sys.executable, "-m", "celery",
        "-A", "dotmac.platform.tasks.celery_app",
        "worker",
        "--loglevel=info",
        "--concurrency=2",
        "--pool=solo"  # Use solo pool for testing (no multiprocessing issues)
    ]

    print(f"Starting Celery worker with command: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Wait for worker to be ready
    print("Waiting for Celery worker to start...")
    for line in process.stdout:
        print(f"  {line.strip()}")
        if "ready" in line.lower() or "started" in line.lower():
            print("✓ Celery worker is ready!")
            break

    return process

def stop_worker(process):
    """Stop the Celery worker gracefully."""
    if process:
        print("Stopping Celery worker...")
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=10)
            print("✓ Celery worker stopped")
        except subprocess.TimeoutExpired:
            print("Force killing Celery worker...")
            process.kill()
            process.wait()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage Celery worker for testing")
    parser.add_argument("action", choices=["start", "test"], help="Action to perform")
    args = parser.parse_args()

    if args.action == "start":
        # Start worker and keep it running
        process = start_worker()
        try:
            process.wait()
        except KeyboardInterrupt:
            stop_worker(process)

    elif args.action == "test":
        # Start worker, run a test task, then stop
        process = start_worker()
        time.sleep(2)  # Give worker time to fully start

        try:
            # Test the worker
            from dotmac.platform.tasks.celery_app import health_check

            print("Testing health check task...")
            result = health_check.apply_async()
            health_status = result.get(timeout=10)
            print(f"✓ Health check result: {health_status}")

        except Exception as e:
            print(f"✗ Test failed: {e}")
        finally:
            stop_worker(process)