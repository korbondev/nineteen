import re
import sys
import subprocess
import tempfile
from collections import defaultdict
from datetime import datetime

# Regular expressions to match the relevant line pattern
LOG_PATTERN = r'(\d+\|sn\d+_m.*)\| (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| INFO \|.*task: ([\w\.-]+) .*streamed \d+ tokens in ([\d\.]+) seconds @ ([\d\.]+) tps.*'
COMPLETION_PATTERN = r'(\d+\|sn\d+_m.*)\| (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| INFO \|.*task: ([\w\.-]+) completed image in ([\d\.]+) seconds.*'

# Number of lines to be provided by argument
num_lines = sys.argv[1]

# Run pm2 logs command and store output to temp file
def run_pm2_logs(num_lines):
    with tempfile.NamedTemporaryFile(delete=False, mode='w+') as temp_file:
        subprocess.run(["pm2", "logs", "--nostream", "--lines", num_lines], stdout=temp_file)
        return temp_file.name

def parse_log_file(file_path):
    task_data = defaultdict(lambda: {"times": [], "tps_values": [], "count": 0, "timestamps": []})
    
    # Read the log file
    with open(file_path, 'r') as f:
        for line in f:
            match = re.match(LOG_PATTERN, line)
            if match:
                # Extract task type, time in seconds, TPS, and timestamp
                timestamp = match.group(2)
                task_type = match.group(3)
                time_in_seconds = float(match.group(4))
                tps = float(match.group(5))
                
                task_data[task_type]["times"].append(time_in_seconds)
                task_data[task_type]["tps_values"].append(tps)
                task_data[task_type]["count"] += 1
                task_data[task_type]["timestamps"].append(timestamp)
            else:
                completion_match = re.match(COMPLETION_PATTERN, line)
                if completion_match:
                    # Extract task type, time in seconds, and timestamp
                    timestamp = completion_match.group(2)
                    task_type = completion_match.group(3)
                    time_in_seconds = float(completion_match.group(4))
                    
                    task_data[task_type]["times"].append(time_in_seconds)
                    task_data[task_type]["count"] += 1
                    task_data[task_type]["timestamps"].append(timestamp)
    
    # Calculate min, max, and average for times and TPS for each task
    results = {}
    for task_type, data in task_data.items():
        times = data["times"]
        tps_values = data["tps_values"]
        timestamps = data["timestamps"]
        
        if times:
            min_time = min(times)
            max_time = max(times)
            avg_time = sum(times) / len(times)
        else:
            min_time = max_time = avg_time = None
        
        if tps_values:
            min_tps = min(tps_values)
            max_tps = max(tps_values)
            avg_tps = sum(tps_values) / len(tps_values)
        else:
            min_tps = max_tps = avg_tps = None
        
        if timestamps:
            date_range = (
                datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M"),
                datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M")
            )
        else:
            date_range = (None, None)
        
        results[task_type] = {
            "min_time": min_time,
            "max_time": max_time,
            "avg_time": avg_time,
            "min_tps": min_tps,
            "max_tps": max_tps,
            "avg_tps": avg_tps,
            "count": data["count"],
            "date_range": date_range
        }
    
    return results

def main():
    temp_file_path = run_pm2_logs(num_lines)
    results = parse_log_file(temp_file_path)
    if results:
        for task_type, stats in results.items():
            print(f"Task: {task_type}")
            print(f"  Count: {stats['count']}")
            if stats["min_time"] is not None:
                print(f"  Minimum time: {stats['min_time']:.4f} seconds")
                print(f"  Maximum time: {stats['max_time']:.4f} seconds")
                print(f"  Average time: {stats['avg_time']:.4f} seconds")
            if stats["min_tps"] is not None:
                print(f"  Minimum TPS: {stats['min_tps']:.4f}")
                print(f"  Maximum TPS: {stats['max_tps']:.4f}")
                print(f"  Average TPS: {stats['avg_tps']:.4f}")
            print(f"  Date Range: {stats['date_range'][0]} to {stats['date_range'][1]}")
            print()
    else:
        print("No valid log entries found.")

if __name__ == "__main__":
    main()