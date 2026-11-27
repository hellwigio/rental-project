terraform {
  required_version = ">= 1.6.0, < 2.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.100"
    }
  }
}

provider "aws" {
  region = "eu-north-1"
  default_tags {
    tags = { Project = "rental-project" }
  }
}

variable "subnet_id" {
  type        = string
  description = "Existing public subnet with a route to an internet gateway in Stockholm."
}

variable "domain" {
  type        = string
  description = "DNS hostname used for the public HTTPS endpoint."
  validation {
    condition     = can(regex("^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$", var.domain))
    error_message = "Use a lowercase DNS hostname without a scheme or path."
  }
}

variable "key_name" {
  type        = string
  description = "Existing EC2 key pair in Stockholm."
}

variable "admin_ipv4" {
  type        = string
  description = "Single IPv4 address allowed to use SSH."
  validation {
    condition     = can(cidrnetmask("${var.admin_ipv4}/32"))
    error_message = "Supply an IPv4 address without a prefix."
  }
}

data "aws_subnet" "app" {
  id = var.subnet_id
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_security_group" "app" {
  name_prefix = "rental-"
  vpc_id      = data.aws_subnet.app.vpc_id
  dynamic "ingress" {
    for_each = toset([80, 443])
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.admin_ipv4}/32"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "app" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.small"
  subnet_id                   = var.subnet_id
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.app.id]
  key_name                    = var.key_name
  user_data                   = templatefile("${path.module}/bootstrap.sh.tftpl", { domain = var.domain })
  tags                        = { Name = "rental-project" }
  metadata_options {
    http_tokens = "required"
  }
  credit_specification {
    cpu_credits = "standard"
  }
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }
  lifecycle {
    prevent_destroy = true
    ignore_changes  = [ami]
  }
}

resource "aws_eip" "app" {
  domain   = "vpc"
  instance = aws_instance.app.id
}

output "public_ipv4" {
  value = aws_eip.app.public_ip
}

output "catalog_url" {
  value = "https://${var.domain}/api/listings/"
}
