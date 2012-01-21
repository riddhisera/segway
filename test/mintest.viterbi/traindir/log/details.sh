## segway 1.2.0.dev-r6121 run 7335ae40beef11e0938400237d9dcf3a at 2011-08-05 00:14:06.105779
/homes/hoffman/arch/Linux-x86_64/bin/gmtkTriangulate -cppCommandOptions "-DCARD_SEG=4 -DCARD_FRAMEINDEX=2000000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1" -outputTriangulatedFile traindir/triangulation/segway.str.4.1.trifile -strFile traindir/segway.str -verbosity 0
/homes/hoffman/arch/Linux-x86_64/bin/gmtkEMtrainNew -base 3 -componentCache F -cppCommandOptions "-DCARD_SEG=4 -DCARD_FRAMEINDEX=2000000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1" -deterministicChildrenStore F -dirichletPriors T -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile ../data/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 0 -nf2 2 -ni1 2 -ni2 0 -objsNotToTrain traindir/auxiliary/dont_train.list -of1 traindir/observations/int.list -of2 traindir/observations/float32.list -storeAccFile traindir/accumulators/acc.0.0.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng 0 -verbosity 0
/homes/hoffman/arch/Linux-x86_64/bin/gmtkEMtrainNew -base 3 -componentCache F -cppCommandOptions "-DCARD_SEG=4 -DOUTPUT_PARAMS_FILENAME=traindir/params/params.0.params.0 -DCARD_FRAMEINDEX=2000000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1" -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile ../data/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 0:0 -lst 100000 -maxEmIters 1 -nf1 0 -nf2 2 -ni1 2 -ni2 0 -objsNotToTrain traindir/auxiliary/dont_train.list -of1 traindir/observations/int.list -of2 traindir/observations/float32.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng nil -verbosity 0
/homes/hoffman/arch/Linux-x86_64/bin/gmtkEMtrainNew -base 3 -componentCache F -cppCommandOptions "-DCARD_SEG=4 -DINPUT_PARAMS_FILENAME=traindir/params/params.0.params.0 -DCARD_FRAMEINDEX=2000000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1" -deterministicChildrenStore F -dirichletPriors T -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile ../data/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 0 -nf2 2 -ni1 2 -ni2 0 -objsNotToTrain traindir/auxiliary/dont_train.list -of1 traindir/observations/int.list -of2 traindir/observations/float32.list -storeAccFile traindir/accumulators/acc.0.0.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng 0 -verbosity 0
/homes/hoffman/arch/Linux-x86_64/bin/gmtkEMtrainNew -base 3 -componentCache F -cppCommandOptions "-DCARD_SEG=4 -DOUTPUT_PARAMS_FILENAME=traindir/params/params.0.params.1 -DINPUT_PARAMS_FILENAME=traindir/params/params.0.params.0 -DCARD_FRAMEINDEX=2000000 -DCARD_SUBSEG=1 -DSEGTRANSITION_WEIGHT_SCALE=1.0" -deterministicChildrenStore F -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile ../data/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -llStoreFile traindir/likelihood/likelihood.ll -lldp 0.001 -loadAccFile traindir/accumulators/acc.0.@D.bin -loadAccRange 0:0 -lst 100000 -maxEmIters 1 -nf1 0 -nf2 2 -ni1 2 -ni2 0 -objsNotToTrain traindir/auxiliary/dont_train.list -of1 traindir/observations/int.list -of2 traindir/observations/float32.list -outputMasterFile traindir/params/output.master -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng nil -verbosity 0