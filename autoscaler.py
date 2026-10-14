import csv
import os
import subprocess
import time
from datetime import datetime

# Configuration variables
IMAGE_NAME = "quadratic-app:latest"  # Aapki Docker image ka naam
NETWORK_NAME = "web-net"
MIN_CONTAINERS = 1
MAX_CONTAINERS = 4
CPU_SCALE_OUT_THRESHOLD = 70.0
CPU_SCALE_IN_THRESHOLD = 30.0
CHECK_INTERVAL = 5  

CSV_FILE = "metrics.csv"


def init_csv():
  if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as f:
      writer = csv.writer(f)
      writer.writerow(
          ["Timestamp", "Container_Name", "CPU_Percent", "Total_Containers"]
      )


def get_running_app_containers():
  cmd = "docker ps --filter 'name=app-container-' --format '{{.Names}}'"
  result = subprocess.run(
      cmd, shell=True, capture_output=True, text=True, check=True
  )
  containers = [
      c.strip() for c in result.stdout.splitlines() if c.strip()
  ]
  return sorted(containers)


def get_container_cpu(container_name):
  cmd = f"docker stats {container_name} --no-stream --format '{{{{.CPUPerc}}}}'"
  result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
  output = result.stdout.strip().replace("%", "")
  try:
    return float(output)
  except ValueError:
    return 0.0


def update_nginx_conf(containers):
  # nginx.conf ke upstream block ko update karna
  upstream_servers = ""
  for c in containers:
    upstream_servers += f"    server {c}:5000;\n"

  nginx_config_content = f"""events {{ worker_connections 1024; }}

http {{
    upstream flask_app {{
{upstream_servers}
    }}

    server {{
        listen 80;

        location / {{
            proxy_pass http://flask_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }}
    }}
}}
"""

  with open("nginx.conf", "w") as f:
    f.write(nginx_config_content)

  # Nginx container ko reload karna bina request drop kiye
  subprocess.run("docker exec nginx-lb nginx -s reload", shell=True)


def scale_out(current_containers):
  if len(current_containers) >= MAX_CONTAINERS:
    print(
        f"[INFO] Max container limit ({MAX_CONTAINERS}) reached. Cannot scale"
        " out."
    )
    return current_containers

  new_container_index = len(current_containers) + 1
  # Agla available port dhoondna (e.g. 5003, 5004...)
  new_port = 5000 + new_container_index
  container_name = f"app-container-{new_container_index}"

  print(f"[SCALE OUT] Starting new container: {container_name} on port {new_port}")
  run_cmd = (
      f"docker run -d --name {container_name} --network {NETWORK_NAME} "
      f"--cpus='0.5' --memory='512m' -p {new_port}:5000 {IMAGE_NAME}"
  )
  subprocess.run(run_cmd, shell=True, check=True)

  updated_containers = get_running_app_containers()
  update_nginx_conf(updated_containers)
  return updated_containers


def scale_in(current_containers):
  if len(current_containers) <= MIN_CONTAINERS:
    print(
        f"[INFO] Min container limit ({MIN_CONTAINERS}) reached. Cannot scale"
        " in."
    )
    return current_containers

  container_to_remove = current_containers[-1]
  print(f"[SCALE IN] Stopping and removing container: {container_to_remove}")

  # Graceful stop with timeout
  subprocess.run(
      f"docker stop -t 10 {container_to_remove}", shell=True, check=True
  )
  subprocess.run(f"docker rm {container_to_remove}", shell=True, check=True)

  updated_containers = get_running_app_containers()
  update_nginx_conf(updated_containers)
  return updated_containers


def main():
  print("=== Starting Python Autoscaler ===")
  init_csv()

  while True:
    try:
      containers = get_running_app_containers()
      if not containers:
        print("[WARNING] No active application containers found!")
        time.sleep(CHECK_INTERVAL)
        continue

      total_cpu = 0.0
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        for c in containers:
          cpu = get_container_cpu(c)
          total_cpu += cpu
          writer.writerow([timestamp, c, cpu, len(containers)])

      avg_cpu = total_cpu / len(containers)
      print(
          f"[{timestamp}] Containers: {len(containers)} | Avg CPU: {avg_cpu:.2f}%"
      )

      # Scaling decisions
      if avg_cpu > CPU_SCALE_OUT_THRESHOLD:
        print(
            f"[TRIGGER] Avg CPU ({avg_cpu:.2f}%) > {CPU_SCALE_OUT_THRESHOLD}%. Scaling"
            " Out..."
        )
        containers = scale_out(containers)
        time.sleep(10)  # Cooldown period after scaling

      elif avg_cpu < CPU_SCALE_IN_THRESHOLD and len(containers) > MIN_CONTAINERS:
        print(
            f"[TRIGGER] Avg CPU ({avg_cpu:.2f}%) < {CPU_SCALE_IN_THRESHOLD}%. Scaling"
            " In..."
        )
        containers = scale_in(containers)
        time.sleep(10)  # Cooldown period after scaling

      time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
      print("\n[INFO] Autoscaler stopped by user.")
      break
    except Exception as e:
      print(f"[ERROR] {e}")
      time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
  main()