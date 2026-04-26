# Nginx Stability and Startup Fix

## Problem Overview
The `hms_nginx` container was frequently failing to start or restarting because of a "race condition." It tried to connect to the `web` container before the Django/Gunicorn application was ready. By default, Nginx crashes if its upstream targets are not resolvable at startup.

## The Fix
This fix consists of three layers of protection:

1.  **Docker Healthchecks**: 
    - The PostgreSQL and Web containers now have automated health monitoring.
    - PostgreSQL uses `pg_isready` to signal it's ready for connections.
    - The Web app uses a internal Python check to ensure the server is responding to HTTP requests.

2.  **Cascading Startup Order**:
    - The Web app now waits for the Database to be **Healthy** before starting.
    - Nginx now waits for the Web app to be **Healthy** before starting.
    - This ensures that every component is ready before the next one tries to connect to it.

3.  **Dynamic DNS Resolution**:
    - The Nginx configuration was updated to use variables for the backend address.
    - This tells Nginx to resolve the hostname `web` only when it's needed, rather than crashing if it's missing at startup.

## Impact on PostgreSQL Database
There is **no negative impact** on your database. Here is what to expect:

- **Data Integrity**: There is absolutely no effect on your data, tables, or schema.
- **Improved Reliability**: The database is now explicitly monitored. If it fails to start correctly, Docker will report it as `unhealthy`, making it much easier to troubleshoot.
- **Boot Safety**: The web application will no longer crash or spam logs with "Database Connection Refused" errors during startup, as it will wait for the DB to be fully initialized.
- **Performance**: The health check is extremely lightweight (`pg_isready`) and does not put any significant load on the database.

## How to Re-apply
If you ever need to apply this fix manually or on a new server, run the script:
`./Documentation/apply_nginx_fix.sh`
