#!/usr/bin/env bash
(%[^ ]+%)/segway-task run train '' chr21 9457281 9480325 1 0 ../test.genomedata,../test.genomedata /tmp/chr21.0002.(%[a-f0-9]{32}%).float32 /tmp/chr21.0002.(%[a-f0-9]{32}%).int asinh_norm 0,1 False None None -base 3 -componentCache F -cppCommandOptions '-DCARD_SEG=4 -DCARD_FRAMEINDEX=25000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1' -deterministicChildrenStore F -dirichletPriors F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 2 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.2.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng 2 -verbosity 0
