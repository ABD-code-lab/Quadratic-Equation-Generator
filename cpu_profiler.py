import csv
import sys
import time

import psutil


def profile_cpu(duration_seconds, interval_seconds, output_path):

    with open(output_path, "w", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["elapsed_seconds", "cpu_percent"])

        elapsed_seconds = 0

        while elapsed_seconds < duration_seconds:
            cpu_percent = psutil.cpu_percent(interval=interval_seconds)
            writer.writerow([elapsed_seconds, cpu_percent])
            output_file.flush()
            elapsed_seconds += interval_seconds


if __name__ == "__main__":
    duration_seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    interval_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 1
    output_path = sys.argv[3] if len(sys.argv) > 3 else "cpu_usage.csv"
    profile_cpu(duration_seconds, interval_seconds, output_path)
