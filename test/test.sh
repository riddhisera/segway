#!/usr/bin/env bash

## test.sh: test segway

## $Revision$
## Copyright 2011-2012 Michael M. Hoffman <mmh1@uw.edu>

set -o nounset -o pipefail -o errexit

if [ $# != 0 ]; then
    echo usage: "$0"
    exit 2
fi

TMPDIR="$(mktemp -dp . "test-$(date +%Y%m%d).XXXXXX")"

echo >&2 "entering directory $TMPDIR"
cd "$TMPDIR"

if [ "${SEGWAY_TEST_CLUSTER_OPT:-}" ]; then
    cluster_arg="--cluster-opt=$SEGWAY_TEST_CLUSTER_OPT"
else
    cluster_arg="--cluster-opt="
fi

# seed from random.randrange(2**32)
SEGWAY_RAND_SEED=203078386 segway --num-labels=4 --max-train-rounds=2 \
    "$cluster_arg" \
    train ../data/test.genomedata traindir
segway "$cluster_arg" \
    identify+posterior ../data/test.genomedata traindir identifydir

# diff
../compare_directory.py ../data/traindir traindir || true # keep going
../compare_directory.py ../data/identifydir identifydir || true
