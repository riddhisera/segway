#!/usr/bin/env python
from __future__ import division, with_statement

"""
run: DESCRIPTION
"""

__version__ = "$Revision$"

# Copyright 2008 Michael M. Hoffman <mmh1@washington.edu>

from errno import ENOENT
from itertools import count, izip
from math import floor, log10
from os import close as os_close, extsep, fdopen, makedirs
from random import random
from shutil import move, rmtree
from string import Template
from struct import calcsize, unpack
import sys
from tempfile import mkstemp

from numpy import amin, amax, array, NAN, NINF, PINF
from numpy.random import uniform
from optbuild import OptionBuilder_ShortOptWithSpace
from path import path
from tables import NoSuchNodeError, openFile

from ._util import (data_filename, data_string, fill_array, NamedTemporaryDir,
                    walk_supercontigs)
from .bed import read
from .importseq import MIN_GAP_LEN

# XXXXXXXXXXXX: this is temporary until the dflt=nan issues are fixed in tables
NAN = 0

# XXX: should be options
NUM_SEGS = 2
MAX_EM_ITERS = 100
VERBOSITY = 0
TEMPDIR_PREFIX = "gmseg-"
COVAR_TIED = True # would need to expand to MC, MX to fix
WIG_DIRNAME = "out"
MAX_SEGMENTS = 1000

# defaults
RANDOM_STARTS = 1

# programs
TRIANGULATE_PROG = OptionBuilder_ShortOptWithSpace("gmtkTriangulate")
EM_TRAIN_PROG = OptionBuilder_ShortOptWithSpace("gmtkEMtrainNew")
VITERBI_PROG = OptionBuilder_ShortOptWithSpace("gmtkViterbiNew")

# extensions and suffixes
EXT_WIG = "wig"
EXT_LIST = "list"
EXT_OUT = "out"

PREFIX_SEGMENT = "segment"


SUFFIX_LIST = extsep + EXT_LIST
SUFFIX_OUT = extsep + EXT_OUT

# templates and formats
RES_STR_TMPL = "seg.str.tmpl"
RES_INPUT_MASTER_TMPL = "input.master.tmpl"
RES_DONT_TRAIN = "dont_train.list"

DENSE_CPT_START_SEG_FRAG = "0 start_seg 0 CARD_SEG"
DENSE_CPT_SEG_SEG_FRAG = "1 seg_seg 1 CARD_SEG CARD_SEG"

MEAN_TMPL = "$index mean_${seg}_${obs} 1 ${rand}"

COVAR_TMPL_TIED = "$index covar_${obs} 1 ${rand}"
COVAR_TMPL_UNTIED = "$index covar_${seg}_${obs} 1 ${rand}" # unused as of yet

MC_TMPL = "$index 1 0 mc_${seg}_${obs} mean_${seg}_${obs} covar_${obs}"
MX_TMPL = "$index 1 mx_${seg}_${obs} 1 dpmf_always mc_${seg}_${obs}"

NAME_COLLECTION_TMPL = "$obs_index collection_seg_${obs} 2"
NAME_COLLECTION_CONTENTS_TMPL = "mx_${seg}_${obs}"

TRACK_FMT = "browser position %s:%s-%s"

# XXX: this could be specified as a dict instead
WIG_HEADER = 'track type=wiggle_0 name=gmseg ' \
    'description="segmentation by gmseg" visibility=dense viewLimits=0:1' \
    'autoScale=off'

TRAIN_ATTRNAMES = ["input_master_filename", "trainable_params_filename"]

# XXX: uses of these two can become methods of Runner, that
# automatically pull in self.tempdirname
def mkstemp_file(*args, **kwargs):
    temp_fd, temp_filename = mkstemp(*args, **kwargs)

    return fdopen(temp_fd, "w+"), temp_filename

def new_extrema(func, data, extrema):
    curr_extrema = func(data, 0)

    return func([extrema, curr_extrema], 0)

def mkstemp_closed(*args, **kwargs):
    temp_fd, temp_filename = mkstemp(*args, **kwargs)
    os_close(temp_fd)

    return temp_filename

def save_template(filename, resource, mapping, tempdirname=None,
                  delete_existing=False):
    """
    creates a temporary file if filename is None or empty
    """
    if filename:
        if not delete_existing and path(filename).exists():
            return filename
        else:
            outfile = open(filename, "w+")
    else:
        resource_part = resource.rpartition(".tmpl")
        stem = resource_part[0] or resource_part[2]
        stem_part = stem.rpartition(".")
        prefix = stem_part[0] + "."
        suffix = "." + stem_part[2]

        outfile, filename = mkstemp_file(suffix, prefix, tempdirname)

    with outfile as outfile:
        tmpl = Template(data_string(resource))
        text = tmpl.substitute(mapping)

        outfile.write(text)

    return filename

#def save_output_master():
#    return data_filename("output.master")

def make_spec(name, items):
    items[:0] = ["%s_IN_FILE inline" % name, str(len(items)), ""]

    return "\n".join(items) + "\n"

# def make_dt_spec(num_obs):
#     return make_spec("DT", ["%d seg_obs%d BINARY_DT" % (index, index)
#                             for index in xrange(num_obs)])

def make_items_multiseg(tmpl, num_segs, num_obs, data=None):
    substitute = Template(tmpl).substitute

    res = []

    for seg_index in xrange(num_segs):
        seg = "seg%d" % seg_index
        for obs_index in xrange(num_obs):
            obs = "obs%d" % obs_index
            mapping = dict(seg=seg, obs=obs,
                           seg_index=seg_index, obs_index=obs_index,
                           index=num_obs*seg_index + obs_index)
            if data is not None:
                mapping["rand"] = data[seg_index, obs_index]

            res.append(substitute(mapping))

    return res

def make_spec_multiseg(name, *args, **kwargs):
    return make_spec(name, make_items_multiseg(*args, **kwargs))

# XXX: numpy
def make_normalized_random_rows(num_rows, num_cols):
    res = []

    for row_index in xrange(num_rows):
        row_raw = []
        for col_index in xrange(num_cols):
            row_raw.append(random())

        total = sum(row_raw)

        res.extend([item_raw/total for item_raw in row_raw])

    return res

def make_random_spec(frag, *args, **kwargs):
    random_rows = make_normalized_random_rows(*args, **kwargs)

    return " ".join([frag] + [str(row) for row in random_rows])

def make_dense_cpt_start_seg_spec(num_segs):
    return make_random_spec(DENSE_CPT_START_SEG_FRAG, 1, num_segs)

def make_dense_cpt_seg_seg_spec(num_segs):
    return make_random_spec(DENSE_CPT_SEG_SEG_FRAG, num_segs, num_segs)

def make_dense_cpt_spec(num_segs):
    items = [make_dense_cpt_start_seg_spec(num_segs),
             make_dense_cpt_seg_seg_spec(num_segs)]

    return make_spec("DENSE_CPT", items)

def make_rands(low, high, num_segs):
    return array([uniform(low, high)
                  for seg_index in xrange(num_segs)])

def make_mean_spec(num_segs, num_obs, mins, maxs):
    rands = make_rands(mins, maxs, num_segs)

    return make_spec_multiseg("MEAN", MEAN_TMPL, num_segs, num_obs, rands)

def make_covar_spec(num_segs, num_obs, mins, maxs):
    if COVAR_TIED:
        num_segs = 1
        tmpl = COVAR_TMPL_TIED
    else:
        tmpl = COVAR_TMPL_UNTIED

    # always start with maximum variance
    data = array([maxs - mins for seg_idnex in xrange(num_segs)])

    return make_spec_multiseg("COVAR", tmpl, num_segs, num_obs, data)

def make_mc_spec(num_segs, num_obs):
    return make_spec_multiseg("MC", MC_TMPL, num_segs, num_obs)

def make_mx_spec(num_segs, num_obs):
    return make_spec_multiseg("MX", MX_TMPL, num_segs, num_obs)

def make_name_collection_spec(num_segs, num_obs):
    num_segs = NUM_SEGS
    substitute = Template(NAME_COLLECTION_TMPL).substitute
    substitute_contents = Template(NAME_COLLECTION_CONTENTS_TMPL).substitute

    items = []

    for obs_index in xrange(num_obs):
        obs = "obs%d" % obs_index

        mapping = dict(obs=obs, obs_index=obs_index)

        contents = [substitute(mapping)]
        for seg_index in xrange(num_segs):
            seg = "seg%d" % seg_index
            mapping = dict(seg=seg, obs=obs,
                           seg_index=seg_index, obs_index=obs_index)

            contents.append(substitute_contents(mapping))
        items.append("\n".join(contents))

    return make_spec("NAME_COLLECTION", items)

def save_observations_gmtk(observation_rows, prefix, tempdirname):
    temp_file, temp_filename = mkstemp_file(".obs", prefix, tempdirname)

    with temp_file as temp_file:
        for observation_row in observation_rows:
            print >>temp_file, " ".join(datum.score
                                        for datum in observation_row)

    return temp_filename

def make_prefix_fmt(num_filenames):
    # make sure there aresufficient leading zeros
    return "%%0%dd." % (int(floor(log10(num_filenames))) + 1)

def read_gmtk_out(infile):
    data = infile.read()

    fmt = "%dL" % (len(data) / calcsize("L"))
    return unpack(fmt, data)

def write_wig(outfile, output, XXXobservations):
    XXX switch to a variableStep output

    first_datum = XXXobservations[0][0]
    last_datum = XXXobservations[-1][0]

    chrom = first_datum.chrom
    start = first_datum.chromStart
    end = last_datum.chromEnd

    print >>outfile, TRACK_FMT % (chrom, start, end)
    print >>outfile, WIG_HEADER

    for score, data in zip(output, XXXobservations):
        # this assumes that the relevant values for all items in data
        # are the same
        #
        # XXX: check this
        datum = data[0]

        row = [datum.chrom, datum.chromStart, datum.chromEnd, str(score)]
        print >>outfile, "\t".join(row)

def load_gmtk_out_save_wig(XXXobservations, gmtk_outfilename, wig_filename):
    with open(gmtk_outfilename) as gmtk_outfile:
        data = read_gmtk_out(gmtk_outfile)

        with open(wig_filename, "w") as wig_file:
            return write_wig(wig_file, data, XXXobservations)

class Runner(object):
    def __init__(self, **kwargs):
        # filenames
        self.h5filenames = None
        self.gmtk_obs_filelistname = None

        self.include_filename = None
        self.input_master_filename = None
        self.structure_filename = None

        self.trainable_params_filename = None
        self.tempdirname = None
        self.log_likelihood_filename = None
        self.dont_train_filename = None

        self.dumpnames_filename = None
        self.output_filelistname = None
        self.output_filenames = None

        self.wig_dirname = WIG_DIRNAME

        # data
        self.mins = None
        self.maxs = None

        # variables
        self.num_segs = NUM_SEGS
        self.random_starts = RANDOM_STARTS

        # flags
        self.delete_existing = False
        self.triangulate = True
        self.train = True # EM train # this should become an int for num_starts
        self.identify = True # viterbi

        self.__dict__.update(kwargs)

    def load_log_likelihood(self):
        with open(self.log_likelihood_filename) as infile:
            return float(infile.read().strip())

    def set_trainable_params_filename(self, new=False):
        # if this is not run and trainable_params_filename is
        # unspecified, then it won't be passed to gmtkViterbiNew

        trainable_params_filename = self.trainable_params_filename
        if not new and trainable_params_filename:
            if (not self.delete_existing
                and path(trainable_params_filename).exists()):
                # it already exists and you don't want to force regen
                self.train = False
        else:
            self.trainable_params_filename = \
                mkstemp_closed(".params", "params-", self.tempdirname)

    def set_log_likelihood_filename(self):
        # XXX: for now, this is always a tempfile

        self.log_likelihood_filename = \
            mkstemp_closed(".ll", "likelihood-", self.tempdirname)

    def make_wig_dir(self):
        wig_dirname = self.wig_dirname
        if self.delete_existing:
            # just always try to delete it
            try:
                rmtree(self.wig_dirname)
            except OSError, err:
                if err.errno != ENOENT:
                    raise

        makedirs(wig_dirname)

    def save_include(self):
        self.include_filename = data_filename("seg.inc")

    def save_structure(self):
        observation_tmpl = Template(data_string("observation.tmpl"))
        observation_sub = observation_tmpl.substitute

        observations = \
            "\n".join(observation_sub(observation_index=observation_index)
                      for observation_index in xrange(self.num_obs))

        mapping = dict(include_filename=self.include_filename,
                       observations=observations)

        self.structure_filename = \
            save_template(self.structure_filename, RES_STR_TMPL, mapping,
                          self.tempdirname, self.delete_existing)

    def save_observations(self):
        prefix_tmpl = PREFIX_SEGMENT + make_prefix_fmt(MAX_SEGMENTS)
        tempdirname = self.tempdirname
        num_obs = None
        segment_index = 0

        temp_file, self.gmtk_obs_filelistname = mkstemp_file(SUFFIX_LIST,
                                                             dir=tempdirname)

        with temp_file as temp_file:
            for h5filename in self.h5filenames:
                with openFile(h5filename) as h5file:
                    for supercontig in walk_supercontigs(h5file):
                        ## read data
                        try:
                            continuous = supercontig.continuous
                        except NoSuchNodeError:
                            continue

                        curr_num_obs = continuous.shape[1]
                        if num_obs is None:
                            ## setup at first array
                            num_obs = curr_num_obs
                            extrema_shape = (num_obs,)
                            mins = fill_array(PINF, extrema_shape)
                            maxs = fill_array(NINF, extrema_shape)
                        else:
                            ## ensure homogeneity
                            assert num_obs == curr_num_obs

                        ## read data
                        observations = continuous.read()

                        ## XXXopt: this could be precomputed
                        mins = new_extrema(amin, observations, mins)
                        maxs = new_extrema(amax, observations, maxs)

                        ## find segments that have less than
                        ## MIN_GAP_LEN missing data gaps in a row
                        ## XXXopt: this could be precomputed
                        mask_nonmissing = (continuous == NAN).sum(1) != num_obs
                        indices_nonmissing = where(mask_nonmissing)

                        starts = []
                        ends = []

                        last_index = -MIN_GAP_LEN
                        for index in indices_nonmissing:
                            if index - last_index >= MIN_GAP_LEN:
                                if starts:
                                    ends.append(last_index)

                                starts.append(index)
                                last_index = index

                        ends.append(last_index)

                        assert len(starts) == len(ends)

                        ## iterate through segments and write
                        for start, end in zip(starts, ends):
                            prefix = prefix_tmpl % segment_index

                            # XXX: add writing of exist data
                            rows = continuous[start:end, ...]
                            filename = save_observations_gmtk(rows, prefix,
                                                              tempdirname)
                            print >>temp_file, filename
                            print >>sys.stderr, filename
                            segment_index += 0

        self.num_obs = num_obs
        self.mins = mins
        self.maxs = maxs

    def save_input_master(self, new=False):
        num_segs = self.num_segs
        num_obs = self.num_obs
        mins = self.mins
        maxs = self.maxs

        include_filename = self.include_filename

        if new:
            input_master_filename = None
        else:
            input_master_filename = self.input_master_filename

        dense_cpt_spec = make_dense_cpt_spec(num_segs)
        mean_spec = make_mean_spec(num_segs, num_obs, mins, maxs)
        covar_spec = make_covar_spec(num_segs, num_obs, mins, maxs)
        mc_spec = make_mc_spec(num_segs, num_obs)
        mx_spec = make_mx_spec(num_segs, num_obs)
        name_collection_spec = make_name_collection_spec(num_segs, num_obs)

        self.input_master_filename = \
            save_template(input_master_filename, RES_INPUT_MASTER_TMPL,
                          locals(), self.tempdirname, self.delete_existing)

    def save_dont_train(self):
        self.dont_train_filename = data_filename(RES_DONT_TRAIN)

    def save_output_filelist(self):
        tempdirname = self.tempdirname

        prefix_tmpl = "out" + make_prefix_fmt(MAX_SEGMENTS)
        output_filenames = \
            [mkstemp_closed(SUFFIX_OUT, prefix_tmpl % index, tempdirname)
             for index in xrange(num_filenames)]

        temp_file, self.output_filelistname = \
            mkstemp_file(SUFFIX_LIST, "output-", tempdirname)

        with temp_file as temp_file:
            for output_filename in output_filenames:
                print >>temp_file, output_filename

        self.output_filenames = output_filenames

    def save_dumpnames(self):
        temp_file, self.dumpnames_filename = \
            mkstemp_file(SUFFIX_LIST, "dumpnames-", self.tempdirname)

        with temp_file as temp_file:
            print >>temp_file, "seg"

    def save_params(self):
        self.save_observations() # do first, because it sets self.num_obs

        self.save_include()
        self.save_structure()

        if self.train:
            self.save_dont_train()
            self.set_trainable_params_filename() # might turn off self.train
            self.set_log_likelihood_filename()

        if self.identify:
            self.save_output_filelist()
            self.save_dumpnames()
            self.make_wig_dir()

    def move_results(self, name, src_filename, dst_filename):
        if dst_filename:
            move(src_filename, dst_filename)
        else:
            dst_filename = src_filename

        setattr(self, name, dst_filename)

    def gmtk_out2wig(self):
        output_filenames = self.output_filenames

        prefix_fmt = make_prefix_fmt(len(output_filenames))
        wig_filebasename_fmt = extsep.join("gmseg", prefix_fmt, EXT_WIG)

        wig_dirpath = path(self.wig_dirname)
        wig_filepath_fmt = wig_dirpath / wig_filebasename_fmt

        zipper = izip(count(), output_filenames, self.XXXobservations_list)
        for index, gmtk_outfilename, XXXobservations in zipper:
            wig_filename = wig_filepath_fmt % index

            XXX going to need to get this data directly from array
            load_gmtk_out_save_wig(XXXobservations, gmtk_outfilename,
                                   wig_filename)

    def run_triangulate(self):
        # XXX: should specify the triangulation file
        TRIANGULATE_PROG(strFile=self.structure_filename,
                         verbosity=VERBOSITY)

    def run_train(self):
        # XXX: this can be a parallel departure point
        kwargs = dict(strFile=self.structure_filename,
                      objsNotToTrain=self.dont_train_filename,
                      llStoreFile=self.log_likelihood_filename,

                      of1=self.gmtk_obs_filelistname,
                      fmt1="ascii",
                      nf1=self.num_obs,
                      ni1=0,

                      maxEmIters=MAX_EM_ITERS,
                      verbosity=VERBOSITY)

        dst_filenames = [self.input_master_filename,
                         self.trainable_params_filename]

        # list of tuples(log_likelihood, input_master_filename,
        #                trainable_params_filename)
        start_params = []

        for start_index in xrange(self.random_starts):
            # XXX: re-add the ability to set your own starting parameters,
            # with new=start_index
            # (copy from existing rather than using it on command-line)
            self.save_input_master(new=True)
            self.set_trainable_params_filename(new=True)

            input_master_filename = self.input_master_filename
            trainable_params_filename = self.trainable_params_filename

            EM_TRAIN_PROG(inputMasterFile=input_master_filename,
                          outputTrainableParameters=trainable_params_filename,
                          **kwargs)

            start_params.append((self.load_log_likelihood(),
                                 input_master_filename,
                                 trainable_params_filename))

        src_filenames = max(start_params)[1:]

        zipper = zip(TRAIN_ATTRNAMES, src_filenames, dst_filenames)
        for name, src_filename, dst_filename in zipper:
            self.move_results(name, src_filename, dst_filename)

    def run_identify(self):
        if not self.input_master_filename:
            self.save_input_master()

        trainable_params_filename = self.trainable_params_filename
        if trainable_params_filename:
            cpp_options = "-DUSE_TRAINABLE_PARAMS"
        else:
            cpp_options = None

        VITERBI_PROG(strFile=self.structure_filename,

                     inputMasterFile=self.input_master_filename,
                     inputTrainableParameters=trainable_params_filename,

                     ofilelist=self.output_filelistname,
                     dumpNames=self.dumpnames_filename,

                     of1=self.gmtk_obs_filelistname,
                     fmt1="ascii",
                     nf1=self.num_obs,
                     ni1=0,

                     cppCommandOptions=cpp_options,
                     verbosity=VERBOSITY)

        self.gmtk_out2wig()

    def __call__(self):
        # XXX: use binary I/O to gmtk rather than ascii
        # XXX: register atexit for cleanup_resources

        try:
            # XXX: allow specification of directory instead of tmp
            with NamedTemporaryDir(prefix=TEMPDIR_PREFIX) as tempdir:
                self.tempdirname = tempdir.name
                self.save_params()

                if self.triangulate:
                    self.run_triangulate()

                # XXX: make tempfile to specify for -jtFile for both
                # em and viterbi
                if self.train:
                    self.run_train()

                if self.identify:
                    self.run_identify()
        finally:
            self.tempdirname = None

def parse_options(args):
    from optparse import OptionParser

    usage = "%prog [OPTION]... H5FILE..."
    version = "%%prog %s" % __version__
    parser = OptionParser(usage=usage, version=version)
    # XXX: group here: filenames
    parser.add_option("--input-master", "-i", metavar="FILE",
                      help="use input master file FILE; "
                      "create if it doesn't exist")

    parser.add_option("--structure", "-s", metavar="FILE",
                      help="use structure file FILE; "
                      "create if it doesn't exist")

    parser.add_option("--trainable-params", "-t", metavar="FILE",
                      help="use trainable parameters file FILE; "
                      "create if it doesn't exist")

    # XXX: group here: variables
    parser.add_option("--random-starts", "-r", type=int, default=RANDOM_STARTS,
                      metavar="NUM",
                      help="randomize start parameters NUM times")

    # XXX: group here: flag options
    parser.add_option("--force", "-f", action="store_true",
                      help="delete any preexisting files")
    parser.add_option("--no-identify", "-I", action="store_true",
                      help="do not identify segments")
    parser.add_option("--no-train", "-T", action="store_true",
                      help="do not train model")

    options, args = parser.parse_args(args)

    if not len(args) == 1:
        parser.print_usage()
        sys.exit(1)

    return options, args

def main(args=sys.argv[1:]):
    options, args = parse_options(args)

    runner = Runner()

    runner.h5filenames = args
    runner.input_master_filename = options.input_master
    runner.structure_filename = options.structure
    runner.trainable_params_filename = options.trainable_params

    runner.random_starts = options.random_starts

    runner.delete_existing = options.force
    runner.train = not options.no_train
    runner.identify = not options.no_identify

    return runner()

if __name__ == "__main__":
    sys.exit(main())
