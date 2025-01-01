#!/usr/bin/env bash

ALLOWED_PATTERNS='QCFlow\(|"QCFlow"|import QCFlow$'
# add globs to this list to ignore them in grep
EXCLUDED_FILES=(
    # ignore typos in i18n files, since they're not controlled by us
    "qcflow/server/js/src/lang/*.json"
)

EXCLUDE_ARGS=""
for pattern in "${EXCLUDED_FILES[@]}"; do
    EXCLUDE_ARGS="$EXCLUDE_ARGS --exclude=$pattern"
done

if grep -InE ' \bM(lf|LF|lF)low\b' $EXCLUDE_ARGS "$@" | grep -vE "$ALLOWED_PATTERNS"; then
    echo -e "\nFound typo for QCFlow spelling in above file(s). Please use 'QCFlow' instead of 'QCFlow'."
    exit 1
else
    exit 0
fi
