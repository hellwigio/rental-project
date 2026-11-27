#!/usr/bin/env bash
set -euo pipefail
: "${1:?Usage: bootstrap.sh SUBNET KEY_NAME ADMIN_IPV4}" "${2:?}" "${3:?}"
export AWS_DEFAULT_REGION=eu-north-1
account=$(aws sts get-caller-identity --query Account --output text)
provider="arn:aws:iam::$account:oidc-provider/token.actions.githubusercontent.com"
existing=$(aws iam list-open-id-connect-providers --query 'OpenIDConnectProviderList[].Arn' --output text)
create=yes
if [[ " ${existing//$'\t'/ } " == *" $provider "* ]]; then create=no; fi
if aws cloudformation describe-stack-resource --stack-name rental-bootstrap --logical-resource-id Provider >/dev/null 2>&1; then create=yes; fi
aws cloudformation deploy --stack-name rental-bootstrap --template-file "$(dirname "$0")/bootstrap.yml" \
  --capabilities CAPABILITY_NAMED_IAM --no-fail-on-empty-changeset \
  --parameter-overrides "Subnet=$1" "KeyName=$2" "AdminIPv4=$3" "CreateProvider=$create"
printf 'AWS account for Run workflow: %s\n' "$account"
