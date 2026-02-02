#!/usr/bin/env python3
"""
Analyze CloudWatch logs to determine active users and their activity.
"""

import json
import re
from datetime import datetime, timedelta, UTC
from collections import defaultdict
import boto3

def analyze_logs():
    """Analyze CloudWatch logs for user activity over the past week."""
    
    # Initialize CloudWatch Logs client
    logs_client = boto3.client('logs', region_name='us-east-1')
    
    # Calculate time range (past 7 days)
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=7)
    
    log_group = "/aws/lambda/amplify-dhi9gcvt4p94z-producti-gamehandler9C35C05F-xkwnhFZkn6yj"
    
    print(f"Analyzing logs from {start_time.isoformat()} to {end_time.isoformat()}")
    print(f"Log group: {log_group}\n")
    
    # Query for all command processing events
    query = """
    fields @timestamp, @message
    | filter @message like /Processing command/
    | parse @message /Processing command '(?<command>[^']+)' for session (?<session_id>[a-f0-9-]+)/
    | sort @timestamp desc
    """
    
    # Start the query
    response = logs_client.start_query(
        logGroupName=log_group,
        startTime=int(start_time.timestamp()),
        endTime=int(end_time.timestamp()),
        queryString=query,
        limit=10000
    )
    
    query_id = response['queryId']
    print(f"Query started: {query_id}")
    print("Waiting for results...")
    
    # Wait for query to complete
    import time
    while True:
        time.sleep(2)
        result = logs_client.get_query_results(queryId=query_id)
        status = result['status']
        
        if status == 'Complete':
            break
        elif status == 'Failed':
            print("Query failed!")
            return
        elif status == 'Cancelled':
            print("Query cancelled!")
            return
    
    # Process results
    results = result['results']
    
    if not results:
        print("No command activity found in the past week.")
        return
    
    # Organize data by session
    sessions = defaultdict(lambda: defaultdict(int))
    session_timestamps = defaultdict(list)
    total_commands = 0
    
    for row in results:
        row_dict = {field['field']: field['value'] for field in row}
        session_id = row_dict.get('session_id', 'unknown')
        command = row_dict.get('command', 'unknown')
        timestamp = row_dict.get('@timestamp', '')
        
        if session_id != 'unknown' and command != 'unknown':
            sessions[session_id][command] += 1
            session_timestamps[session_id].append(timestamp)
            total_commands += 1
    
    # Calculate statistics
    unique_sessions = len(sessions)
    
    print(f"\n{'='*80}")
    print(f"ACTIVITY SUMMARY (Past 7 Days)")
    print(f"{'='*80}\n")
    print(f"Total Active Users (Sessions): {unique_sessions}")
    print(f"Total Commands Executed: {total_commands}")
    print(f"Average Commands per User: {total_commands / unique_sessions:.1f}")
    
    # Top commands across all users
    all_commands = defaultdict(int)
    for session_data in sessions.values():
        for cmd, count in session_data.items():
            all_commands[cmd] += count
    
    print(f"\n{'='*80}")
    print(f"TOP COMMANDS (All Users)")
    print(f"{'='*80}\n")
    sorted_commands = sorted(all_commands.items(), key=lambda x: x[1], reverse=True)
    for i, (cmd, count) in enumerate(sorted_commands[:20], 1):
        percentage = (count / total_commands) * 100
        print(f"{i:2d}. {cmd:20s} - {count:4d} times ({percentage:5.1f}%)")
    
    # User engagement levels
    print(f"\n{'='*80}")
    print(f"USER ENGAGEMENT LEVELS")
    print(f"{'='*80}\n")
    
    engagement_levels = {
        'Very Active (50+ commands)': 0,
        'Active (20-49 commands)': 0,
        'Moderate (10-19 commands)': 0,
        'Light (5-9 commands)': 0,
        'Minimal (1-4 commands)': 0
    }
    
    for session_id, commands in sessions.items():
        total = sum(commands.values())
        if total >= 50:
            engagement_levels['Very Active (50+ commands)'] += 1
        elif total >= 20:
            engagement_levels['Active (20-49 commands)'] += 1
        elif total >= 10:
            engagement_levels['Moderate (10-19 commands)'] += 1
        elif total >= 5:
            engagement_levels['Light (5-9 commands)'] += 1
        else:
            engagement_levels['Minimal (1-4 commands)'] += 1
    
    for level, count in engagement_levels.items():
        percentage = (count / unique_sessions) * 100 if unique_sessions > 0 else 0
        print(f"{level:30s}: {count:3d} users ({percentage:5.1f}%)")
    
    # Top 10 most active users
    print(f"\n{'='*80}")
    print(f"TOP 10 MOST ACTIVE USERS")
    print(f"{'='*80}\n")
    
    sorted_sessions = sorted(
        sessions.items(),
        key=lambda x: sum(x[1].values()),
        reverse=True
    )
    
    for i, (session_id, commands) in enumerate(sorted_sessions[:10], 1):
        total = sum(commands.values())
        top_commands = sorted(commands.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Get session duration
        timestamps = session_timestamps[session_id]
        if len(timestamps) > 1:
            first = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
            last = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
            duration = (last - first).total_seconds() / 60  # minutes
            duration_str = f"{duration:.1f} minutes"
        else:
            duration_str = "< 1 minute"
        
        print(f"{i:2d}. Session: {session_id[:8]}...")
        print(f"    Total Commands: {total}")
        print(f"    Session Duration: {duration_str}")
        print(f"    Top Commands:")
        for cmd, count in top_commands:
            print(f"      - {cmd}: {count} times")
        print()

if __name__ == '__main__':
    analyze_logs()
