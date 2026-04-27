terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_key_pair" "v2" {
  key_name   = "${var.project_name}-key"
  public_key = file(var.public_key_path)
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
  filter {
    name   = "state"
    values = ["available"]
  }
}

resource "aws_vpc" "v2" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "v2" {
  vpc_id = aws_vpc.v2.id
  tags   = { Name = "${var.project_name}-igw" }
}

resource "aws_subnet" "v2" {
  vpc_id                  = aws_vpc.v2.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project_name}-subnet" }
}

resource "aws_route_table" "v2" {
  vpc_id = aws_vpc.v2.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.v2.id
  }
  tags = { Name = "${var.project_name}-rt" }
}

resource "aws_route_table_association" "v2" {
  subnet_id      = aws_subnet.v2.id
  route_table_id = aws_route_table.v2.id
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_security_group" "v2" {
  name        = "${var.project_name}-sg"
  description = "Kit Platform V2: SSH, Frontend 3010, API 8010"
  vpc_id      = aws_vpc.v2.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_cidrs
  }

  ingress {
    description = "Frontend Next.js"
    from_port   = 3010
    to_port     = 3010
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "API FastAPI"
    from_port   = 8010
    to_port     = 8010
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-sg" }
}

locals {
  user_data = <<-EOT
#!/bin/bash
set -e
yum update -y
yum install -y docker
systemctl enable docker
systemctl start docker
curl -sL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
mkdir -p /usr/local/lib/docker/cli-plugins
ln -sf /usr/local/bin/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose
ARCH=$$(uname -m); [ "$$ARCH" = "x86_64" ] && ARCH=amd64
curl -sSL "https://github.com/docker/buildx/releases/download/v0.19.0/buildx-v0.19.0.linux-$${ARCH}" -o /usr/local/lib/docker/cli-plugins/docker-buildx
chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx
usermod -aG docker ec2-user
echo "Docker ready."
EOT
}

resource "aws_instance" "v2" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.v2.key_name
  subnet_id              = aws_subnet.v2.id
  vpc_security_group_ids = [aws_security_group.v2.id]
  user_data              = local.user_data
  user_data_replace_on_change = true

  root_block_device {
    volume_size = var.root_volume_size_gb
    volume_type = "gp3"
  }

  tags = { Name = var.project_name }
}
