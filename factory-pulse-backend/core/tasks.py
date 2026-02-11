import time
import logging
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

logger = logging.getLogger(__name__)

# Task 1: Sanity Check (Simple)
@shared_task(name='core.sum_sanity_check')
def sum_sanity_check(a, b):
    logger.info(f"Executing sanity check with {a} and {b}")
    time.sleep(5)  # Simulates delay
    return a + b

# Task 2: Realistic (OEE Report Processing with Retry)
@shared_task(bind=True, max_retries=3, name='core.generate_oee_report')
def generate_oee_report(self, machine_id):
    try:
        logger.info(f"Starting report generation for machine {machine_id}")
        # Simulates integration with a heavy database or external service
        time.sleep(3) 
        
        # Simulates a random network error to test Retry mechanism
        if int(time.time()) % 2 == 0:
            raise ConnectionError("Simulated network failure while fetching telemetry.")
            
        return {"machine_id": machine_id, "status": "completed", "oee": 85.4}
        
    except ConnectionError as exc:
        logger.warning(f"Connection error. Retrying: {exc}")
        # Exponential backoff: 5s, 10s, 20s...
        raise self.retry(exc=exc, countdown=5 * (2 ** self.request.retries))
    except SoftTimeLimitExceeded:
        logger.error("Task time limit exceeded! Performing cleanup...")
        return {"status": "error", "reason": "timeout"}