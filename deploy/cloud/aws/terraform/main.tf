terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "container_image" {
  type = string
}

variable "db_username" {
  type    = string
  default = "knoema"
}

variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_vpc" "knoema" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.knoema.id
  cidr_block        = "10.42.1.0/24"
  availability_zone = "${var.region}a"
}

resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.knoema.id
  cidr_block        = "10.42.2.0/24"
  availability_zone = "${var.region}b"
}

resource "aws_security_group" "api" {
  name   = "knoema-api"
  vpc_id = aws_vpc.knoema.id
}

resource "aws_lb" "api" {
  name               = "knoema-api"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.api.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_ecs_cluster" "knoema" {
  name = "knoema"
}

resource "aws_ecs_task_definition" "api" {
  family                   = "knoema-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.container_image
      essential = true
      portMappings = [{ containerPort = 8000, hostPort = 8000 }]
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = "knoema-api"
  cluster         = aws_ecs_cluster.knoema.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups = [aws_security_group.api.id]
  }
}

resource "aws_db_subnet_group" "postgres" {
  name       = "knoema-postgres"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_db_instance" "postgres" {
  allocated_storage      = 20
  db_name                = "knoema"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t4g.micro"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  skip_final_snapshot    = true
  publicly_accessible    = false
  vpc_security_group_ids = [aws_security_group.api.id]
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "knoema-redis"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "knoema-redis"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.api.id]
}

output "load_balancer_dns" {
  value = aws_lb.api.dns_name
}
