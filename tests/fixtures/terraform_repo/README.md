# infra

Terraform configuration that provisions an S3 artifacts bucket.

```bash
terraform init
terraform plan -var project=demo
terraform apply -var project=demo
```

No automated tests or CI are configured yet.
