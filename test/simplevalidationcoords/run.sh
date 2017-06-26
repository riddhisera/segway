#!/usr/bin/env bash

## test.sh: test segway
## run this from the parent

## $Revision$
## Copyright 2011-2012 Michael M. Hoffman <michael.hoffman@utoronto.ca>

set -o nounset -o pipefail -o errexit

if [ $# != 0 ]; then
    echo usage: "$0"
    exit 2
fi

testdir="$(mktemp -dp . "test-$(date +%Y%m%d).XXXXXX")"

echo >&2 "entering directory $testdir"
cd "$testdir"

if [ "${SEGWAY_TEST_CLUSTER_OPT:-}" ]; then
    cluster_arg="--cluster-opt=$SEGWAY_TEST_CLUSTER_OPT"
else
    cluster_arg="--cluster-opt="
fi

set -x

# seed from python -c "import random; print random.randrange(2**32)"
SEGWAY_RAND_SEED=203078386 segway --num-labels=4 --max-train-rounds=2 \
    --include-coords="../include-coords.txt" \
    --minibatch-fraction=0.1 \
    --split-sequences=25000 \
    --validation-coords="../validation-coords.txt" \
    "$cluster_arg" \
    train ../test.genomedata traindir

segway "$cluster_arg" \
    identify+posterior ../test.genomedata traindir identifydir

cd ..

../compare_directory.py ../simplevalidationcoords/touchstone ../simplevalidationcoords/${testdir#"./"}
