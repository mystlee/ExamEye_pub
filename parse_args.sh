#!/bin/bash

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --*)
            OPTION="${1/--/}"
            VALUE="$2"
            eval "${OPTION}='${VALUE}'"
            shift 2
            ;;
        -*)
            OPTION="${1/-/}"
            VALUE="$2"
            eval "${OPTION}='${VALUE}'"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done
