# 🚦 Traffic Generator with Burst Mode & Kubernetes Deployment

A lightweight Python-based TCP traffic generator with dynamic rate control, burst capabilities, and a sleek UI — ideal for **HPA testing**, **network experiments**, and **observability** projects.

---

## 📁 Project Structure
traffic-control/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── sender.py
│   ├── templates/
│   ├── static/
│   ├── requirements.txt
├── Dockerfile
├── .dockerignore
├── k8s/
│   ├── traffic-generator.yaml
│   ├── traffic-receiver.yaml
│   ├── traffic-configmap.yaml

---

## ⚙️ Local Setup (Dev)

### 1. 🐍 Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

2. 📦 Install dependencies
pip install -r requirements.txt


3. 🚀 Start the app locally
Transmitter:
 RECEIVER_SERVICE=127.0.0.1 RECEIVER_PORT=8888 python3 app/main.py
Receiver:
 nc -lk 8888

🐳 Build Docker Image
Make sure you're in the project root:
docker build -t traffic-generator:latest .

To test locally:
docker run --rm -p 5050:5050 traffic-generator:latest

☸️ Kubernetes Deployment
1. ⛵ Apply manifests
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/traffic-generator.yaml
kubectl apply -f k8s/traffic-receiver.yaml

| Stage / need                                                            | Suggested level | Why                                                                                                                                                       |
| ----------------------------------------------------------------------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Day-to-day production** (cluster is stable, dashboards in place)      | `WARNING`       | • Keeps the console almost silent.<br>• Still prints DNS failures, TCP connect errors, or burst overrides—early signs that something is wrong.            |
| **Routine testing / demo** (you want to see rate & burst updates)       | `INFO`          | • Adds one-line confirmations when you click “Apply Rate”, start/stop a burst, or when pods join/leave.<br>• Still low-noise; packet loops aren’t logged. |
| **Debug session** (chasing an intermittent issue)                       | `DEBUG`         | • Full detail: config snapshots, per-thread actions, etc. Turn it on temporarily, then revert.                                                            |
| **Post-mortem log scrape only** (everything is monitored by Prometheus) | `ERROR`         | • Logs *only* fatal exceptions. Smallest footprint but you lose early warnings.                                                                           |


2. 🌐 Access Traffic Generator UI

Use the NodePort service URL:
# find Node IP & port:
kubectl get svc traffic-generator-service

🧪 Features

    ✅ Adjustable traffic rate (ms between packets)

    💥 Burst mode with duration

    ⏸️ Traffic pause/resume

    📊 Real-time status bar

    ✨ Blinking status on burst

    ⚓ Headless TCP receiver (for internal testing)

    📦 Dockerized & Kubernetes ready

    📈 Optional integration with Prometheus + Grafana (coming soon)


🧼 Deactivate venv
to leave the Python environment:
deactivate

(You re-created a new virtual environment using: 
python3 -m venv venv
source venv/bin/activate
Creating a new virtual environment means it starts empty — no packages are installed inside it. 
You now need to install Flask again inside this environment.
⚠️ Run this after activating the virtual environment: pip install -r requirements.txt)


Test the docker container locally (linux) like this:

    Terminal A:

nc -lk 8888

    Terminal B:

docker run --rm --network=host \
  -e RECEIVER_SERVICE=127.0.0.1 \
  -e RECEIVER_PORT=8888 \
  traffic-generator:latest

👥 Authors

    Luigi — App creator and UX vision
    Kubernetes (ChatGPT) — DevOps, Infra, and automation support

📜 License

MIT License. Use freely and responsibly.


---

📌 **Place this `README.md` file** at the root of your project (same level as `Dockerfile`).

Would you like me to also add `LICENSE`, `.gitignore`, or even GitHub Actions workflows later on?
