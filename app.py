import random
import socket

from flask import Flask, jsonify, render_template

app = Flask(__name__)


def generate_coefficients():
    coefficient_a = random.randint(-10, 10)

    while coefficient_a == 0:
        coefficient_a = random.randint(-10, 10)

    coefficient_b = random.randint(-10, 10)
    coefficient_c = random.randint(-10, 10)

    return coefficient_a, coefficient_b, coefficient_c


def solve_quadratic(coefficient_a, coefficient_b, coefficient_c):
    discriminant = coefficient_b ** 2 - 4 * coefficient_a * coefficient_c

    if discriminant > 0:
        sqrt_discriminant = discriminant ** 0.5
        root_one = (-coefficient_b + sqrt_discriminant) / (2 * coefficient_a)
        root_two = (-coefficient_b - sqrt_discriminant) / (2 * coefficient_a)

        return {"solution_type": "two_real_roots", "roots": [round(root_one, 4), round(root_two, 4)]}

    if discriminant == 0:
        root = -coefficient_b / (2 * coefficient_a)

        return {"solution_type": "one_real_root", "roots": [round(root, 4)]}

    real_part = round(-coefficient_b / (2 * coefficient_a), 4)
    imaginary_part = round((abs(discriminant) ** 0.5) / (2 * coefficient_a), 4)

    return {
        "solution_type": "no_real_roots",
        "roots": [f"{real_part} + {imaginary_part}i", f"{real_part} - {imaginary_part}i"],
    }


def get_server_identity():
    hostname = socket.gethostname()
    probe_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        probe_socket.connect(("8.8.8.8", 80))
        ip_address = probe_socket.getsockname()[0]

    except OSError:
        ip_address = socket.gethostbyname(hostname)

    finally:
        probe_socket.close()

    return hostname, ip_address


@app.route("/")
def index():

    return render_template("index.html")


@app.route("/api/solve", methods=["GET"])
def solve():

    coefficient_a, coefficient_b, coefficient_c = generate_coefficients()
    solution = solve_quadratic(coefficient_a, coefficient_b, coefficient_c)
    hostname, ip_address = get_server_identity()

    return jsonify(
        {
            "a": coefficient_a,
            "b": coefficient_b,
            "c": coefficient_c,
            "solution_type": solution["solution_type"],
            "roots": solution["roots"],
            "hostname": hostname,
            "ip_address": ip_address,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
