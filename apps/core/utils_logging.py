import logging
import os

# Configure Audit Logger
audit_logger = logging.getLogger('hms_audit')
audit_logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

if os.environ.get("VERCEL"):
    # Serverless: filesystem is read-only, so log to stdout instead.
    # Vercel captures stdout automatically and shows it in the dashboard's Logs tab.
    handler = logging.StreamHandler()
else:
    # Local dev: keep writing to a real log file
    LOG_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'logs'
    )
    os.makedirs(LOG_DIR, exist_ok=True)
    handler = logging.FileHandler(os.path.join(LOG_DIR, 'hms_audit.log'))

handler.setFormatter(formatter)
audit_logger.addHandler(handler)


def log_admin_action(user, action, details):
    """
    Helper to log admin actions.
    """
    message = f"User: {user.username} | Action: {action} | Details: {details}"
    audit_logger.info(message)
