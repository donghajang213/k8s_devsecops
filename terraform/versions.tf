terraform {
    required_version = ">= 1.15"
    required_providers {
        google = {
            source = "hashicorp/google"
            version = "~> 6.0"   # 실제 최신 안정 버전 확인해서 채우기
        }
    }
}