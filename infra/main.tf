terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = "us-east-1"
}

variable "public_key" {
  description = "Conteúdo da chave pública SSH (arquivo .pub)"
  type        = string
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_ecr_repository" "app" {
  name         = "tarefas-app"
  force_delete = true
}

resource "aws_key_pair" "key" {
  key_name   = "tarefas-key"
  public_key = var.public_key
}

resource "aws_security_group" "sg" {
  name        = "tarefas-sg"
  description = "Acesso web, SSH e Grafana"

  dynamic "ingress" {
    for_each = [22, 80, 3000]
    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# A EC2 precisa de permissão para baixar a imagem do ECR
resource "aws_iam_role" "ec2" {
  name = "tarefas-ec2-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_read" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_instance_profile" "profile" {
  name = "tarefas-profile"
  role = aws_iam_role.ec2.name
}

resource "aws_instance" "server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.small"
  key_name               = aws_key_pair.key.key_name
  vpc_security_group_ids = [aws_security_group.sg.id]
  iam_instance_profile   = aws_iam_instance_profile.profile.name

  root_block_device {
    volume_size = 20
  }

  user_data = <<-EOF
    #!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose-v2
    snap install aws-cli --classic
    usermod -aG docker ubuntu
    systemctl enable --now docker
  EOF

  tags = { Name = "tarefas-server" }
}

resource "aws_eip" "ip" {
  instance = aws_instance.server.id
}

output "ip_publico" {
  value = aws_eip.ip.public_ip
}

output "ecr_url" {
  value = aws_ecr_repository.app.repository_url
}
