terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
  }
}

provider "google" {
  project = "ai-connect-sap26blr-307"
  region  = "us-central1"
  zone    = "us-central1-c"
}

# -------------------------------
# VPC Network
# -------------------------------
resource "google_compute_network" "vpc_network" {
  name                    = "terraform-hackathon-network"
  auto_create_subnetworks = true
}

# -------------------------------
# Firewall: Frontend + Backend
# -------------------------------
resource "google_compute_firewall" "allow_web" {
  name    = "allow-frontend-backend"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["5173", "8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["hackathon-vm"]
}

# -------------------------------
# Compute Engine VM
# -------------------------------
resource "google_compute_instance" "vm_instance" {
  name         = "terraform-hackathon-vm"
  machine_type = "e2-standard-4" # 4 vCPU, 16 GB RAM
  zone         = "us-central1-c"
  tags         = ["hackathon-vm"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 50
    }
  }

  network_interface {
    network = google_compute_network.vpc_network.name
    access_config {} # Public IP
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -e

    echo "===== Installing Docker ====="
    apt-get update
    apt-get install -y ca-certificates curl gnupg git

    curl -fsSL https://get.docker.com | sh

    echo "===== Installing Docker Compose v2 ====="
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.29.2/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

    systemctl enable docker
    systemctl start docker

    echo "===== Allow docker without sudo ====="
    usermod -aG docker $USER

    echo "===== Cloning project from GitHub ====="
    cd /opt
    git clone https://github.com/LastAirbender07/security-manager-AI-Connect.git
    chown -R $USER:$USER security-manager-AI-Connect

    echo "===== Starting Docker stack ====="
    cd /opt/security-manager-AI-Connect/security-manager-main
    chmod +x start_all.sh
    ./start_all.sh

    echo "===== Startup completed ====="
  EOT
}

# -------------------------------
# Outputs
# -------------------------------
output "vm_public_ip" {
  description = "Public IP of the Hackathon VM"
  value       = google_compute_instance.vm_instance.network_interface[0].access_config[0].nat_ip
}
