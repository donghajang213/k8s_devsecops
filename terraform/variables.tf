variable "project_id" {
    type    = string
    description = "k8s-devsecops-dh"
}

variable "region" {
    type = string
    default = "asia-northeast3" # 서울 리전
}

variable "db_user" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_name" {
  type      = string
  sensitive = true
}