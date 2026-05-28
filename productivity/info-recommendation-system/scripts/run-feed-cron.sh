#!/bin/bash
# Cron wrapper script for info-feed
# Used by cronjob with no_agent=True
cd /home/wangsiji/projects/info-feed
python3 feed.py 2>&1
