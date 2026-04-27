# Deploy Kit Platform V2 pe AWS EC2

## Pasul 1 – Creează infrastructura (o singură dată)

```bash
cd kit-platform-v2/infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Editează terraform.tfvars: setează public_key_path la cheia ta publică SSH

# AWS credentials (dacă nu ai deja)
aws configure
# sau: export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...

terraform init
terraform plan
terraform apply
```

Notează **IP-ul EC2** din output (`public_ip`).

## Pasul 2 – Deploy aplicația

Din rădăcina `kit-platform-v2`:

```bash
./infra/scripts/deploy-from-local.sh ec2-user@<IP_EC2>
```

Cu cheie SSH explicită:

```bash
KIT_V2_SSH_KEY=~/.ssh/id_ed25519 ./infra/scripts/deploy-from-local.sh ec2-user@<IP_EC2>
```

## Pasul 3 – Trimite contabilei link-ul

```
http://<IP_EC2>:3010
```

Aplicația rulează pe:
- **Frontend**: port 3010
- **API**: port 8010 (docs: http://IP:8010/docs)

## Update (redeploy)

```bash
./infra/scripts/deploy-from-local.sh ec2-user@<IP_EC2>
```
