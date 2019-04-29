# Specify provider versions & config

terraform {
  required_version = ">= 0.11.13"
  backend          "local"          {}
}

provider "aws" {
  region = "eu-west-1"
}

provider "aws.datascience" {
  region = "eu-west-1"
}
