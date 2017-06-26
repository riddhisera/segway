## segway (%[^ ]+%) run (%[0-9a-f]{32}%) at (%[0-9]{4}%)-(%[0-9]{2}%)-(%[0-9]{2}%) (%[0-9]{2}%):(%[0-9]{2}%):(%[0-9]{2}%).(%[0-9]{1,}%)
(%[^ ]+%)/gmtkTriangulate -cppCommandOptions '-DCARD_SEG=4 -DCARD_FRAMEINDEX=25000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1' -outputTriangulatedFile traindir/triangulation/segway.str.4.1.trifile -strFile traindir/segway.str -verbosity 0
(%[^ ]+%)/segway-task save gmtk-observation-files '' chr21 9549460 9572504 1 0 ../test.genomedata,../test.genomedata traindir/observations/validation/chr21.0000.float32 traindir/observations/validation/chr21.0000.int asinh_norm 0,1 '[Window(world=0, chrom='"'"'chr21'"'"', start=9549460, end=9572504), Window(world=0, chrom='"'"'chr21'"'"', start=9572504, end=9595548)]'
(%[^ ]+%)/segway-task save gmtk-observation-files '' chr21 9572504 9595548 1 0 ../test.genomedata,../test.genomedata traindir/observations/validation/chr21.0001.float32 traindir/observations/validation/chr21.0001.int asinh_norm 0,1 '[Window(world=0, chrom='"'"'chr21'"'"', start=9549460, end=9572504), Window(world=0, chrom='"'"'chr21'"'"', start=9572504, end=9595548)]'
(%[^ ]+%)/segway-task run train '' chr21 9457281 9480325 1 0 ../test.genomedata,../test.genomedata /tmp/chr21.0002.(%[a-f0-9]{32}%).float32 /tmp/chr21.0002.(%[a-f0-9]{32}%).int asinh_norm 0,1 False None None -base 3 -componentCache F -cppCommandOptions '-DCARD_SEG=4 -DCARD_FRAMEINDEX=25000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1' -deterministicChildrenStore F -dirichletPriors F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 2 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.2.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng 2 -verbosity 0
(%[^ ]+%)/segway-task run bundle-train '' 0 0 0 1 0 -base 3 -componentCache F -cppCommandOptions '-DCARD_SEG=4 -DOUTPUT_PARAMS_FILENAME=traindir/params/params.0.params.0 -DCARD_FRAMEINDEX=25000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1' -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 2 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 2 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng nil -verbosity 0
(%[^ ]+%)/segway-task run validate traindir/likelihood/validation.output.ll 0 0 0 1 0 -base 3 -cliqueTableNormalize 0.0 -componentCache F -cppCommandOptions '-DCARD_SEG=4 -DINPUT_PARAMS_FILENAME=traindir/params/params.0.params.0 -DCARD_FRAMEINDEX=25000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1' -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lst 100000 -nf1 2 -nf2 0 -ni1 0 -ni2 2 -obsNAN T -of1 traindir/observations/validation/float32.list -of2 traindir/observations/validation/int.list -probE T -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -verbosity 0
(%[^ ]+%)/segway-task run train '' chr21 9526413 9549460 1 0 ../test.genomedata,../test.genomedata /tmp/chr21.0005.(%[a-f0-9]{32}%).float32 /tmp/chr21.0005.(%[a-f0-9]{32}%).int asinh_norm 0,1 False None None -base 3 -componentCache F -cppCommandOptions '-DCARD_SEG=4 -DINPUT_PARAMS_FILENAME=traindir/params/params.0.params.0 -DCARD_FRAMEINDEX=25000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1' -deterministicChildrenStore F -dirichletPriors F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 2 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.5.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng 5 -verbosity 0
(%[^ ]+%)/segway-task run bundle-train '' 0 0 0 1 0 -base 3 -componentCache F -cppCommandOptions '-DCARD_SEG=4 -DOUTPUT_PARAMS_FILENAME=traindir/params/params.0.params.1 -DINPUT_PARAMS_FILENAME=traindir/params/params.0.params.0 -DCARD_FRAMEINDEX=25000 -DCARD_SUBSEG=1 -DSEGTRANSITION_WEIGHT_SCALE=1.0' -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 5 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 2 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng nil -verbosity 0
(%[^ ]+%)/segway-task run validate traindir/likelihood/validation.output.ll 0 0 0 1 0 -base 3 -cliqueTableNormalize 0.0 -componentCache F -cppCommandOptions '-DCARD_SEG=4 -DINPUT_PARAMS_FILENAME=traindir/params/params.0.params.1 -DCARD_FRAMEINDEX=25000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1' -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lst 100000 -nf1 2 -nf2 0 -ni1 0 -ni2 2 -obsNAN T -of1 traindir/observations/validation/float32.list -of2 traindir/observations/validation/int.list -probE T -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -verbosity 0
