# Data Extraction Scheduling

**Cron** is a command-line tool that schedules tasks to run automatically at specific times. It is used here as an example scheduling the data extraction tasks so as to have a consistent polling of the online information.

## Cron Setup Instructions

- **Edit your crontab:**
  ```sh
  crontab -e
  ```
- **Add the cron job:**
  ```sh
  0 */6 * * * /path/to/python3 /path/to/your_chosen_extractor.py >> /path/to/logfile.log 2>&1
  ```
- Replace `/path/to/python3` and `/path/to/your_chosen_extractor.py` with the **absolute paths** on your machine.
- `0 */6 * * *` means the job runs at minute 0, every 6 hours, every day.