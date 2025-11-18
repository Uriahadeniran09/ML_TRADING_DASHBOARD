#!/bin/bash
# Setup cron job to run daily stock update at 4:30 PM ET Monday-Friday

# Cron schedule: 30 16 * * 1-5 (4:30 PM ET, Mon-Fri)
# Note: Adjust for timezone - if server is UTC, use 30 21 * * 1-5 (9:30 PM UTC = 4:30 PM ET)

CRON_SCHEDULE="30 16 * * 1-5"
DOCKER_COMMAND="docker exec ml_trading_backend python /app/scripts/daily_update.py >> /var/log/stock_update.log 2>&1"

# Add to crontab if not already present
(crontab -l 2>/dev/null | grep -v "daily_update.py"; echo "$CRON_SCHEDULE $DOCKER_COMMAND") | crontab -

echo "Cron job installed:"
echo "$CRON_SCHEDULE $DOCKER_COMMAND"
echo ""
echo "Logs will be written to: /var/log/stock_update.log"
echo ""
echo "To view crontab: crontab -l"
echo "To remove: crontab -e (then delete the line)"
