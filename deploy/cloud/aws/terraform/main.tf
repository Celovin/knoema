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
  default = "luvoire"
}

variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_vpc" "luvoire" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.luvoire.id
  cidr_block        = "10.42.1.0/24"
  availability_zone = "${var.region}a"
}

resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.luvoire.id
  cidr_block        = "10.42.2.0/24"
  availability_zone = "${var.region}b"
}

resource "aws_security_group" "api" {
  name   = "luvoire-api"
  vpc_id = aws_vpc.luvoire.id
}

resource "aws_lb" "api" {
  name               = "luvoire-api"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.api.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_ecs_cluster" "luvoire" {
  name = "luvoire"
}

resource "aws_ecs_task_definition" "api" {
  family                   = "luvoire-api"
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
  name            = "luvoire-api"
  cluster         = aws_ecs_cluster.luvoire.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups = [aws_security_group.api.id]
  }
}

resource "aws_db_subnet_group" "postgres" {
  name       = "luvoire-postgres"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_db_instance" "postgres" {
  allocated_storage      = 20
  db_name                = "luvoire"
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
  name       = "luvoire-redis"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "luvoire-redis"
  engine               = "redis"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.api.id]
}

output "load_balancer_dns" {
  value = aws_lb.api.dns_name
}
