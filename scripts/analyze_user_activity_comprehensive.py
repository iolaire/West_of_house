#!/usr/bin/env python3
"""
Comprehensive analysis of CloudWatch logs for user activity.
Analyzes both log groups and provides detailed statistics.
"""

import json
import re
from datetime import datetime, timedelta, UTC
from collections import defaultdict, Counter
import boto3

def analyze_comprehensive():
    """Analyze CloudWatch logs comprehensively for user activity."""
    
    logs_client = boto3.client('logs', region_name='us-east-1')
    
    # Calculate time range (past 30 days to capture more data)
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=30)
    
    # Both log groups
    log_groups = [
        "/aws/lambda/amplify-dhi9gcvt4p94z-producti-gamehandler9C35C05F-xkwnhFZkn6yj",
        "/aws/lambda/amplify-dhi9gcvt4p94z-producti-gamehandler9C35C05F-HTCiTC81lnDU"
    ]
    
    print(f"Analyzing logs from {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
    print(f"Time range: Past 30 days\n")
    
    all_sessions = defaultdict(lambda: {'commands': defaultdict(int), 'timestamps': []})
    
    for log_group in log_groups:
        print(f"Querying {log_group.split('/')[-1]}...")
        
        query = """
        fields @timestamp, @message
        | filter @message like /Processing command/
        | parse @message /Processing command '(?<command>[^']+)' for session (?<session_id>[a-f0-9-]+)/
        | sort @timestamp desc
        | limit 10000
        """
        
        response = logs_client.start_query(
            logGroupName=log_group,
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString=query,
            limit=10000
        )
        
        query_id = response['queryId']
        
        # Wait for query to complete
        import time
        while True:
            time.sleep(2)
            result = logs_client.get_query_results(queryId=query_id)
            if result['status'] == 'Complete':
                break
        
        # Process results
        for row in result.get('results', []):
            row_dict = {field['field']: field['value'] for field in row}
            session_id = row_dict.get('session_id')
            command = row_dict.get('command')
            timestamp = row_dict.get('@timestamp')
            
            if session_id and command:
                all_sessions[session_id]['commands'][command] += 1
                if timestamp:
                    all_sessions[session_id]['timestamps'].append(timestamp)
    
    # Calculate statistics
    unique_sessions = len(all_sessions)
    total_commands = sum(sum(s['commands'].values()) for s in all_sessions.values())
    
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE ACTIVITY SUMMARY (Past 30 Days)")
    print(f"{'='*80}\n")
    print(f"📊 Total Active Users (Unique Sessions): {unique_sessions}")
    print(f"⌨️  Total Commands Executed: {total_commands}")
    if unique_sessions > 0:
        print(f"📈 Average Commands per User: {total_commands / unique_sessions:.1f}")
    
    # Top commands across all users
    all_commands = Counter()
    for session_data in all_sessions.values():
        for cmd, count in session_data['commands'].items():
            all_commands[cmd] += count
    
    print(f"\n{'='*80}")
    print(f"TOP 20 COMMANDS (All Users)")
    print(f"{'='*80}\n")
    for i, (cmd, count) in enumerate(all_commands.most_common(20), 1):
        percentage = (count / total_commands) * 100 if total_commands > 0 else 0
        print(f"{i:2d}. {cmd:30s} - {count:4d} times ({percentage:5.1f}%)")
    
    # User engagement levels
    print(f"\n{'='*80}")
    print(f"USER ENGAGEMENT LEVELS")
    print(f"{'='*80}\n")
    
    engagement_levels = {
        'Very Active (50+ commands)': [],
        'Active (20-49 commands)': [],
        'Moderate (10-19 commands)': [],
        'Light (5-9 commands)': [],
        'Minimal (1-4 commands)': []
    }
    
    for session_id, data in all_sessions.items():
        total = sum(data['commands'].values())
        if total >= 50:
            engagement_levels['Very Active (50+ commands)'].append((session_id, total))
        elif total >= 20:
            engagement_levels['Active (20-49 commands)'].append((session_id, total))
        elif total >= 10:
            engagement_levels['Moderate (10-19 commands)'].append((session_id, total))
        elif total >= 5:
            engagement_levels['Light (5-9 commands)'].append((session_id, total))
        else:
            engagement_levels['Minimal (1-4 commands)'].append((session_id, total))
    
    for level, users in engagement_levels.items():
        count = len(users)
        percentage = (count / unique_sessions) * 100 if unique_sessions > 0 else 0
        print(f"{level:35s}: {count:3d} users ({percentage:5.1f}%)")
    
    # Top 15 most active users
    print(f"\n{'='*80}")
    print(f"TOP 15 MOST ACTIVE USERS")
    print(f"{'='*80}\n")
    
    sorted_sessions = sorted(
        all_sessions.items(),
        key=lambda x: sum(x[1]['commands'].values()),
        reverse=True
    )
    
    for i, (session_id, data) in enumerate(sorted_sessions[:15], 1):
        total = sum(data['commands'].values())
        top_commands = sorted(data['commands'].items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Calculate session duration
        timestamps = data['timestamps']
        if len(timestamps) > 1:
            try:
                times = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
                duration = (max(times) - min(times)).total_seconds() / 60
                duration_str = f"{duration:.1f} minutes"
            except:
                duration_str = "unknown"
        else:
            duration_str = "< 1 minute"
        
        print(f"{i:2d}. Session: {session_id[:16]}...")
        print(f"    Total Commands: {total}")
        print(f"    Session Duration: {duration_str}")
        print(f"    Top Commands:")
        for cmd, count in top_commands:
            print(f"      - {cmd}: {count} times")
        print()
    
    # Command categories
    print(f"{'='*80}")
    print(f"COMMAND CATEGORIES")
    print(f"{'='*80}\n")
    
    movement_commands = ['north', 'south', 'east', 'west', 'North', 'East', 'West', 'go north', 'go south', 'go east', 'go west', 'go in', 'go inside', 'go out', 'go up', 'go down', 'enter', 'enter window', 'down', 'up']
    interaction_commands = ['look', 'Look', 'examine', 'inspect', 'read', 'read parchment', 'look at', 'look around', 'look in']
    object_commands = ['take', 'drop', 'open', 'close', 'open mailbox', 'take parchment', 'open window', 'close mailbox']
    utility_commands = ['inventory', 'restart', 'RESTART', 'RESET', 'reset']
    
    movement_count = sum(all_commands[cmd] for cmd in movement_commands if cmd in all_commands)
    interaction_count = sum(all_commands[cmd] for cmd in interaction_commands if cmd in all_commands)
    object_count = sum(all_commands[cmd] for cmd in object_commands if cmd in all_commands)
    utility_count = sum(all_commands[cmd] for cmd in utility_commands if cmd in all_commands)
    other_count = total_commands - (movement_count + interaction_count + object_count + utility_count)
    
    print(f"🚶 Movement Commands:    {movement_count:4d} ({movement_count/total_commands*100:5.1f}%)")
    print(f"👁️  Interaction Commands: {interaction_count:4d} ({interaction_count/total_commands*100:5.1f}%)")
    print(f"🎒 Object Commands:      {object_count:4d} ({object_count/total_commands*100:5.1f}%)")
    print(f"⚙️  Utility Commands:     {utility_count:4d} ({utility_count/total_commands*100:5.1f}%)")
    print(f"❓ Other Commands:       {other_count:4d} ({other_count/total_commands*100:5.1f}%)")
    
    # Daily activity breakdown
    print(f"\n{'='*80}")
    print(f"DAILY ACTIVITY BREAKDOWN")
    print(f"{'='*80}\n")
    
    daily_activity = defaultdict(lambda: {'sessions': set(), 'commands': 0})
    
    for session_id, data in all_sessions.items():
        for timestamp in data['timestamps']:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_key = dt.strftime('%Y-%m-%d')
                daily_activity[date_key]['sessions'].add(session_id)
                daily_activity[date_key]['commands'] += 1
            except:
                pass
    
    for date in sorted(daily_activity.keys(), reverse=True):
        sessions_count = len(daily_activity[date]['sessions'])
        commands_count = daily_activity[date]['commands']
        print(f"{date}: {sessions_count:3d} users, {commands_count:4d} commands")

if __name__ == '__main__':
    analyze_comprehensive()
