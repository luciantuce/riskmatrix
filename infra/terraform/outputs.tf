output "public_ip" {
  description = "IP public EC2"
  value       = aws_instance.v2.public_ip
}

output "app_url" {
  description = "URL aplicație (trimite contabilei)"
  value       = "http://${aws_instance.v2.public_ip}:3010"
}

output "api_docs_url" {
  value = "http://${aws_instance.v2.public_ip}:8010/docs"
}

output "deploy_command" {
  value = "KIT_V2_SSH_KEY=~/.ssh/id_ed25519 ./infra/scripts/deploy-from-local.sh ec2-user@${aws_instance.v2.public_ip}"
}
