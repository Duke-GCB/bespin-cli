#!/bin/bash

# Validate a bespin-workflows repo

set -e

REPO="$1"
VERSION="$2"

# Validate the workflows
for workflow in $REPO/*.cwl; do
  python bespin/validate_workflow.py $VERSION $workflow
done
