#!/bin/bash

# Validate a bespin-workflows repo

set -e

REPO="$1"
VERSION="$2"
ERRORS=""

# Check for changelog

if [ ! -f "${REPO}/CHANGELOG.md" ]; then
  echo "CHANGELOG.md not found!"
  ERRORS=1
fi

# Check for README

if [ ! -f "${REPO}/README.md" ]; then
  echo "README.md not found!"
  ERRORS=1
fi

if [ -e "${REPO}/.gitmodules" ]; then
  echo "gitmodules should be gone"
  ERRORS=1
fi

REQUIREMENTS=$(cat "${REPO}/requirements.txt")

# Check for requirements.txt
if [ "$REQUIREMENTS" != "cwltool==1.0.20181217162649" ]; then
  echo "requirements.txt should just be one line"
  ERRORS=1
fi

IGNORE=$(cat "${REPO}/.gitignore")

# Check for .gitignore
if [ "$IGNORE" != "venv" ]; then
  echo "gitignore  should just be one line"
  ERRORS=1
fi

CIRCLECI_CHECKSUM=$(md5 -q "${REPO}/.circleci/config.yml" )
# Check for .gitignore
if [ "$CIRCLECI_CHECKSUM" != "a3fc50d6b91ad53b38b24ccdf14f5a1f" ]; then
  echo "Update the circleci config"
  ERRORS=1
fi

if [ "$ERRORS" != "" ]; then
  echo "Failed"
  exit 1
fi

set -e

# Check if .cwl files exist in repo
ls ${REPO}/*.cwl > /dev/null

# Validate the workflows
for workflow in ${REPO}/*.cwl; do
  python bespin/validate_workflow.py $VERSION $workflow
done

echo "Succeeded"
