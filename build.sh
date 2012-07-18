#!/bin/sh

set -e

print_usage()
{
  echo "Usage: $0 (deb|rpm|all) <version>"
}

if [ $# -lt 2 ]; then
  print_usage
  exit 1
fi

case "$1" in
  "deb")
    ./build-deb.sh $2
    ;;
  "rpm")
    ./build-rpm.sh $2
    ;;
  "all")
    ./build-deb.sh $2
    ./build-rpm.sh $2
    ;;
  *)
    print_usage
    ;;
esac

