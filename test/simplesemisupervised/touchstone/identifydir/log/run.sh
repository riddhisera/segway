## segway (%[^ ]+%) run (%[0-9a-f]{32}%) at (%[0-9]{4}%)-(%[0-9]{2}%)-(%[0-9]{2}%) (%[0-9]{2}%):(%[0-9]{2}%):(%[0-9]{2}%).(%[0-9]{1,}%)
(%[^ ]+%)/gmtkTriangulate -cppCommandOptions "-DCARD_SEG=4 -DCARD_SUPERVISIONLABEL=-1 -DCARD_FRAMEINDEX=200000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=1" -outputTriangulatedFile identifydir/triangulation/segway.str.4.1.trifile -strFile traindir/segway.str -verbosity 0
(%[^ ]+%)/gmtkViterbi -base 3 -cVitRegexFilter ^seg$ -cliqueTableNormalize 0.0 -componentCache F -cppCommandOptions "-DCARD_SEG=4 -DCARD_SUPERVISIONLABEL=-1 -DINPUT_PARAMS_FILENAME=traindir/params/params.params -DCARD_FRAMEINDEX=200000 -DCARD_SUBSEG=1 -DSEGTRANSITION_WEIGHT_SCALE=1.0" -deterministicChildrenStore F -eVitRegexFilter ^seg$ -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile identifydir/log/jt_info.txt -lst 100000 -mVitValsFile - -nf1 2 -nf2 0 -ni1 0 -ni2 2 -obsNAN T -of1 identifydir/observations/float32.list -of2 identifydir/observations/int.list -pVitRegexFilter ^seg$ -strFile traindir/segway.str -triFile identifydir/triangulation/segway.str.4.1.trifile -verbosity 0 -vitCaseSensitiveRegexFilter T
