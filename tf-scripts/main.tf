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

resource "google_compute_network" "vpc_network" {
  name = "terraform-hackathon-network"
}

# need a public compute engine with docker and docker compose installed
# This vm if for our gcp hackthon 
resource "google_compute_instance" "vm_instance" {
  name         = "terraform-hackathon-vm"
  machine_type = "e2-medium"
  zone         = "us-central1-c"

  boot_disk {
    initialize_params {
          image = "debian-cloud/debian-12"
    }
  }

  network_interface {
    network = google_compute_network.vpc_network.name
    access_config {}
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
    export PATH=$PATH:/usr/bin
    export PATH=$PATH:/usr/local/bin
    sudo systemctl start docker
    sudo systemctl enable docker
  EOT
}
