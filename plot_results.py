import csv

import matplotlib.pyplot as plt


def plot_response_time(input_path, output_path):
    request_rates = []
    response_times = []

    with open(input_path, newline="") as input_file:
        reader = csv.DictReader(input_file)

        for row in reader:
            request_rates.append(float(row["request_rate"]))
            response_times.append(float(row["avg_response_time_ms"]))

    plt.figure()
    plt.plot(request_rates, response_times, marker="o")
    plt.xlabel("Request Rate (req/sec)")

    plt.ylabel("Average Response Time (ms)")
    plt.title("Average Response Time vs Request Rate")
    plt.grid(True)

    plt.savefig(output_path)
    plt.close()


def plot_cpu_usage(input_path, output_path):
    elapsed_seconds = []
    cpu_percent_values = []

    with open(input_path, newline="") as input_file:
        reader = csv.DictReader(input_file)

        for row in reader:
            elapsed_seconds.append(float(row["elapsed_seconds"]))
            cpu_percent_values.append(float(row["cpu_percent"]))

    plt.figure()
    plt.plot(elapsed_seconds, cpu_percent_values, color="orange")
    plt.xlabel("Time (seconds)")

    plt.ylabel("CPU Utilization (%)")
    plt.title("CPU Utilization During Load Test")
    plt.grid(True)

    plt.savefig(output_path)
    plt.close()


if __name__ == "__main__":
    plot_response_time("httperf_results.csv", "response_time_graph.png")
    plot_cpu_usage("cpu_usage.csv", "cpu_utilization_graph.png")
