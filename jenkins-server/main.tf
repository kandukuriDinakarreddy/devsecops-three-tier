# main.tf

# 1. Create a Security Group
resource "aws_security_group" "jenkins_sg" {
  name        = "jenkins-management-sg"
  description = "Open ports for Jenkins, SonarQube, and SSH"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # For learning purposes; restrict to your IP in production
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9000
    to_port     = 9000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. Define the EC2 Instance
resource "aws_instance" "jenkins_server" {
  ami                    = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS AMI for us-east-1
  instance_type          = "t2.large"              # Recommended size to comfortably run Jenkins + SonarQube
  key_name               = "your-ec2-key-name"     # Replace with your actual AWS Key Pair name
  vpc_security_group_ids = [aws_security_group.jenkins_sg.id]
  user_data              = file("install_tools.sh")

  tags = {
    Name = "Jenkins-DevSecOps-Master"
  }

  root_block_device {
    volume_size = 30 # Gives enough room for Docker layers and tools
  }
}

# 3. Output the Public IP
output "jenkins_public_ip" {
  value = aws_instance.jenkins_server.public_ip
}

