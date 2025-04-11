# NOTE: This script is only useful for running the model on a remote machine. If you want to run the model on your local machine, you can use the `vllm` command directly.
# This script sets up a VLLM model server on a remote machine using SSH and port forwarding.
# It checks for GPU availability, starts the model, and handles cleanup on exit.
# It also includes signal handling for graceful termination.
# This script is designed to be run as a standalone program.
# It uses the paramiko library for SSH connections and subprocess for process management.
# It also uses the xml.etree.ElementTree library for parsing XML output from nvidia-smi.
# It is important to ensure that the necessary libraries are installed and that the SSH keys are properly configured for passwordless access to the remote machines.
# The script is structured to allow for easy modification and extension, such as adding more machines or changing the model configuration.
# Thanks to Zayne Sprague for the original code/

# vllm_server.py

import paramiko
import subprocess
import socket
import time
import xml.etree.ElementTree as ET
import os
import signal
import threading
import sys
import atexit
import json
from key_handler import (
    KeyHandler,
)  # Assuming you have a module to handle sensitive keys
import argparse

# Global list to keep track of running servers
running_servers = []


def cleanup_servers():
    """Cleanup function to stop all running servers."""
    for server in running_servers:
        server.stop()
    running_servers.clear()
    print("All servers have been stopped.")


# Register the cleanup function to be called at exit
atexit.register(cleanup_servers)


# Register signal handlers
def signal_handler(sig, frame):
    print("Termination signal received. Cleaning up...")
    cleanup_servers()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class Machine:
    def __init__(
        self,
        hostname,
        username,
        key_filename,
        requires_double_hop=False,
        intermediate_host=None,
    ):
        self.hostname = hostname
        self.username = username
        self.key_filename = key_filename
        self.requires_double_hop = requires_double_hop
        self.intermediate_host = (
            intermediate_host  # Should be a Machine instance or dict
        )


class VLLMModelServer:
    def __init__(self, model_name, required_gpus, machines, allowed_gpus=None):
        self.model_name = model_name
        self.required_gpus = required_gpus
        self.allowed_gpus = allowed_gpus  # List of GPU indices allowed for the model
        self.machines = machines  # List of Machine instances
        self.machine = None  # The machine where the model is running
        self.local_port = None  # Local port for accessing the model
        self.process = None  # SSH process
        self.remote_pid_file = None  # Remote PID file
        self.is_running = False  # Flag to indicate if the model is running
        self.lock = threading.Lock()  # To make start/stop thread-safe

    def start(self):
        with self.lock:
            if self.is_running:
                print("Model is already running.")
                return

            # Attempt to launch the model on available machines
            for machine in self.machines:
                print(f"Attempting to launch model on {machine.hostname}")
                if self._launch_model_on_machine(machine):
                    self.is_running = True
                    print(
                        f"Model is running on {self.machine.hostname} and accessible at {self.get_url()}"
                    )
                    return
            print("Failed to launch the model on any machine.")

    def stop(self):
        with self.lock:
            if not self.is_running:
                print("Model is not running.")
                return
            self._terminate_port_forwarding()
            self.is_running = False
            print("Model has been stopped.")

    def get_url(self):
        if self.local_port:
            return f"http://127.0.0.1:{self.local_port}"
        else:
            return None

    def _launch_model_on_machine(self, machine):
        available_gpus = self._check_gpu_availability(machine)
        if available_gpus:
            local_port = self._start_model(machine, available_gpus)
            if local_port:
                self.machine = machine
                self.local_port = local_port
                return True
        return False

    def _check_gpu_availability(self, machine):
        """Check if the required number of GPUs are available on the remote machine."""
        allowed_processes = ["/usr/lib/xorg/Xorg", "/usr/bin/gnome-shell"]
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                machine.hostname,
                username=machine.username,
                key_filename=machine.key_filename,
            )
            stdin, stdout, stderr = client.exec_command("nvidia-smi -q -x")
            output = stdout.read().decode()
        except Exception as e:
            print(f"Error connecting to {machine.hostname}: {e}")
            return []
        finally:
            client.close()

        if not output:
            print(f"No output from nvidia-smi on {machine.hostname}")
            return []

        available_gpus = []
        try:
            root = ET.fromstring(output)
            gpus = root.findall("gpu")
            for gpu in gpus:
                gpu_index = gpu.find("minor_number").text
                processes = gpu.find("processes")
                non_generic_processes = []
                if processes is not None:
                    for process_info in processes.findall("process_info"):
                        process_name = process_info.find("process_name").text
                        if process_name not in allowed_processes:
                            non_generic_processes.append(process_name)
                if not non_generic_processes:
                    available_gpus.append(gpu_index)
                else:
                    print(
                        f"GPU {gpu_index} on {machine.hostname} is used by processes: {non_generic_processes}"
                    )
        except ET.ParseError as e:
            print(
                f"Error parsing XML output from nvidia-smi on {machine.hostname}: {e}"
            )
            return []

        if self.allowed_gpus:
            available_gpus = [gpu for gpu in available_gpus if gpu in self.allowed_gpus]

        if len(available_gpus) >= self.required_gpus:
            print(f"{len(available_gpus)} GPUs are available on {machine.hostname}")
            return available_gpus[: self.required_gpus]
        else:
            print(
                f"Only {len(available_gpus)} GPUs are available on {machine.hostname}"
            )
            return []

    def _start_model(self, machine, available_gpus):
        """Start the model on the remote machine and set up port forwarding."""
        # Find an open port on the remote machine
        model_port = self._find_remote_free_port(machine)
        if not model_port:
            print(f"Could not find an open port on {machine.hostname}")
            return None

        # Find a free local port for port forwarding
        local_port = self._find_free_port()

        # Prepare the CUDA_VISIBLE_DEVICES string
        cuda_visible_devices = ",".join(available_gpus)
        # if 'fuji' in self.machine.hostname:
        # start_command = (
        #     "cd /data2/users/anirudh/; source venv/bin/activate; "
        #     f"HUGGING_FACE_HUB_TOKEN={KeyHandler.hf_key} "
        #     "HF_HOME=/data2/users/anirudh/nlp-models/ "
        #     f"CUDA_VISIBLE_DEVICES={cuda_visible_devices} "
        #     "vllm serve "
        #     f"{self.model_name} "
        #     f"--port {model_port} "
        #     "--host localhost "
        #     "--dtype auto "
        #     f"--tensor-parallel-size {len(available_gpus)} --trust-remote-code "
        #     f"--chat-template /data2/users/anirudh/llama_template.jinja"
        #     # "--gpu-memory-utilization 0.9 "  # Increase GPU memory usage
        #     # "--max-model-len 9120"         # Reduce max sequence length
        # )
        # else:
        # Construct the start command with placeholders replaced
        if self.model_name == "meta-llama/Meta-Llama-3-8B":
            start_command = (
                "cd /datastor1/anirudh/; source venv/bin/activate; "
                f"HUGGING_FACE_HUB_TOKEN={KeyHandler.hf_key} "
                "HF_HOME=/datastor1/anirudh/nlp-models/ "
                f"CUDA_VISIBLE_DEVICES={cuda_visible_devices} "
                "vllm serve "
                f"{self.model_name} "
                f"--port {model_port} "
                "--host localhost "
                "--dtype auto "
                f"--tensor-parallel-size {len(available_gpus)} --trust-remote-code "
                f"--chat-template /datastor1/anirudh/llama_template.jinja"
                # "--gpu-memory-utilization 0.9 "  # Increase GPU memory usage
                # "--max-model-len 9120"         # Reduce max sequence length
            )
        else:
            start_command = (
                "cd /datastor1/anirudh/; source venv/bin/activate; "
                f"HUGGING_FACE_HUB_TOKEN={KeyHandler.hf_key} "
                "HF_HOME=/datastor1/anirudh/nlp-models/ "
                f"CUDA_VISIBLE_DEVICES={cuda_visible_devices} "
                "vllm serve "
                f"{self.model_name} "
                f"--port {model_port} "
                "--host localhost "
                "--dtype auto "
                f"--tensor-parallel-size {len(available_gpus)} --trust-remote-code "
                # "--gpu-memory-utilization 0.9 "  # Increase GPU memory usage
                # "--max-model-len 9120"         # Reduce max sequence length
            )

        # Modify the start command to write the model's PID to a file
        self.remote_pid_file = (
            f"/tmp/model_{machine.username}_{machine.hostname}_{model_port}.pid"
        )
        remote_command = f"""
bash -c '
{start_command} &
echo $! > {self.remote_pid_file}
'
"""

        # Build the SSH command as a list
        ssh_command = [
            "ssh",
            "-i",
            machine.key_filename,
            "-L",
            f"{local_port}:localhost:{model_port}",
        ]

        if machine.requires_double_hop:
            intermediate = machine.intermediate_host
            if isinstance(intermediate, dict):
                intermediate_user = intermediate["username"]
                intermediate_host = intermediate["hostname"]
            else:
                print(f"Invalid intermediate host configuration for {machine.hostname}")
                return None
            ssh_command.extend(["-J", f"{intermediate_user}@{intermediate_host}"])

        ssh_command.append(f"{machine.username}@{machine.hostname}")
        ssh_command.append(remote_command)

        # Start the SSH session and keep it open
        try:
            self.process = subprocess.Popen(
                ssh_command,
                preexec_fn=os.setsid,  # To ensure the process is in its own session
                # stdout=subprocess.DEVNULL,
                # stderr=subprocess.STDOUT
            )
            print(f"Started model on {machine.hostname} with command: {start_command}")
            print(
                f"Port forwarding established from local port {local_port} to {machine.hostname}:{model_port}"
            )
        except Exception as e:
            print(f"Failed to start SSH session: {e}")
            return None

        # Wait until the model is live by checking if the port is listening
        is_live = False
        for _ in range(60 * 20):  # Wait up to 60 seconds for the model to start
            time.sleep(1)
            if self._check_remote_port(machine, model_port):
                print(f"Model is live on {machine.hostname}:{model_port}")
                is_live = True
                break

        if not is_live:
            print(f"Model did not start on {machine.hostname}")
            self._terminate_port_forwarding()
            return None

        return local_port  # Return the local port for API access

    def _find_free_port(self):
        """Find an available port on the local machine."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def _find_remote_free_port(self, machine):
        """Find an available port on the remote machine."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                machine.hostname,
                username=machine.username,
                key_filename=machine.key_filename,
            )
            stdin, stdout, stderr = client.exec_command(
                "python -c 'import socket; s=socket.socket(); s.bind((\"\",0)); print(s.getsockname()[1]); s.close()'"
            )
            port = stdout.read().decode().strip()
        except Exception as e:
            print(f"Error finding free port on {machine.hostname}: {e}")
            return None
        finally:
            client.close()
        if port.isdigit():
            return int(port)
        else:
            print(f"Could not find a free port on {machine.hostname}")
            return None

    def _check_remote_port(self, machine, port):
        """Check if the remote port is listening."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                machine.hostname,
                username=machine.username,
                key_filename=machine.key_filename,
            )
            stdin, stdout, stderr = client.exec_command(
                f"netstat -an | grep LISTEN | grep {port}"
            )
            output = stdout.read().decode().strip()
        except Exception as e:
            print(f"Error checking remote port on {machine.hostname}: {e}")
            return False
        finally:
            client.close()
        return bool(output)

    def _terminate_port_forwarding(self):
        """Terminate the port forwarding process and the remote model process."""
        # Terminate the SSH process
        if self.process:
            if self.process.poll() is None:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    self.process.wait()
                    print(
                        f"Port forwarding process terminated for {self.machine.hostname}"
                    )
                except ProcessLookupError:
                    print(f"Process {self.process.pid} does not exist.")
                except Exception as e:
                    print(f"Error terminating process: {e}")
            else:
                print(f"Process {self.process.pid} has already terminated.")
        else:
            print("No SSH process to terminate.")

        # SSH into the remote machine and kill the model process using the PID file
        if self.remote_pid_file and self.machine:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            retries = 3
            i = 0
            while i < retries:
                i += 1
                try:
                    client.connect(
                        self.machine.hostname,
                        username=self.machine.username,
                        key_filename=self.machine.key_filename,
                    )
                    # Read the PID from the PID file
                    stdin, stdout, stderr = client.exec_command(
                        f"cat {self.remote_pid_file}"
                    )
                    pid = stdout.read().decode().strip()
                    if pid.isdigit():
                        print(
                            f"Terminating remote model process with PID {pid} on {self.machine.hostname}"
                        )
                        client.exec_command(f"kill {pid}; rm {self.remote_pid_file}")
                    else:
                        print(
                            f"No PID file found at {self.remote_pid_file} on {self.machine.hostname}"
                        )
                except Exception as e:
                    print(f"Error ({i+1}) terminating remote process: {e}")
                finally:
                    client.close()


def serve_vllm_model(model, gpus, machines, allowed_gpus=None):
    server = VLLMModelServer(
        model_name=model,
        required_gpus=gpus,
        machines=machines,
        allowed_gpus=allowed_gpus,
    )
    server.start()
    if server.is_running:
        running_servers.append(server)
    return server


# Define your machines

# Once you have the machines defined, you can use them to create a server.
vllm_machine = Machine(
    hostname="hostname",
    username="username",
    key_filename="/path/to/private/key",
    requires_double_hop=False,
    # intermediate_host={'hostname': 'intermediate_hostname', 'username': 'intermediate_username'}
    # or intermediate_host=Machine(hostname='intermediate_hostname', username='intermediate_username', key_filename='/path/to/intermediate/key')
)

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--config", type=str, required=True, help="Model name to serve"
    )
    args = argparser.parse_args()
    config = json.load(open(args.config, "r"))
    model = config["model"]
    gpus_allowed = 2
    if "gpus" in config:
        gpus_allowed = config["gpus"]
    server1 = serve_vllm_model(
        model=model,
        gpus=gpus_allowed,
        machines=[vllm_machine],
        allowed_gpus=["1", "2", "3", "4"],
    )

    with open(f"server_url_{model.split('/')[-1]}.txt", "w") as f:
        f.write(server1.get_url())

    print(f"Model 1 is accessible at {server1.get_url()}")

    while True:
        q = input('Enter "stop" to stop the model server: ')
        if q == "stop":
            server1.stop()
            break
        else:
            print("Invalid input. Please try again.")
