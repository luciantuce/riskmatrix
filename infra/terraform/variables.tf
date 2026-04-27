variable "aws_region" {
  description = "Regiunea AWS"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Nume proiect"
  type        = string
  default     = "kit-platform-v2"
}

variable "instance_type" {
  description = "Tip instanță EC2"
  type        = string
  default     = "t3.small"
}

variable "public_key_path" {
  description = "Cale către cheia ta publică SSH (ex: ~/.ssh/id_ed25519.pub)"
  type        = string
}

variable "ssh_cidrs" {
  description = "CIDR-uri permise pentru SSH"
  type        = list(string)
  default     = ["0.0.0.0/0", "86.120.247.243/32"]
}

variable "root_volume_size_gb" {
  type    = number
  default = 25
}
