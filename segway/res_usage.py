#!/usr/bin/env python
from __future__ import division

"""
res_usage: measure resource_usage
"""

__version__ = "$Revision$"

# Copyright 2009 Michael M. Hoffman <mmh1@washington.edu>

from collections import defaultdict
from math import ceil
from operator import itemgetter
from uuid import uuid1
import sys

from numpy import arange, float32, square
from numpy.random import standard_normal
from optbuild import OptionBuilder_ShortOptWithSpace
from tabdelim import DictWriter

from .run import (EM_TRAIN_PROG, VITERBI_PROG, POSTERIOR_PROG,
                  PREFIX_JOB_NAME_VITERBI, PREFIX_JOB_NAME_POSTERIOR,
                  NAME_BUNDLE_PLACEHOLDER, Runner)
from ._util import fill_array, ISLAND_BASE_NA, ISLAND_LST_NA

MAX_NUM_TRACKS = 20 # XXX: should be 50 or maybe 100
MIN_EXPONENT = 4
MAX_EXPONENT = 6

# XXX: I should replace this with a more general linear model of
# mem_per_obs, these values are for 20 tracks
# XXX: this model should be bootstrapped by res_usage.py and printed
# out with num_tracks = 0
MAX_MEM_PER_OBS = dict(gmtkEMtrainNew=6233,
                       gmtkJT=4034,
                       gmtkViterbiNew=23644)

CHROM_FMT = "fake%d"

DIR_FMT = "res_usage_%d"
TRACKNAME_FMT = "obs%d"

FIELDNAMES = ["program", "num_tracks", "island_base", "island_lst",
              "mem_per_obs", "cpu_per_obs"]

QACCT_PROG = OptionBuilder_ShortOptWithSpace("qacct")

PREFIX2PROG = {PREFIX_JOB_NAME_VITERBI: VITERBI_PROG,
               PREFIX_JOB_NAME_POSTERIOR: POSTERIOR_PROG}

# N1 Grid Engine User's Guide chapter 3 page 71
SGE_MEM_SIZE_SUFFIXES = dict(K=2**10, M=2**20, G=2**30,
                             k=1e3, m=1e6, g=1e9)

# set once per file run
UUID = uuid1().hex

def make_job_name_stem(uuid):
    return "ru%s" % uuid

def make_job_name_stem_uuid():
    return make_job_name_stem(UUID)

class MemUsageRunner(Runner):
    """
    finds memory usage instead of using real data
    """
    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        self.max_em_iters = 1
        self.skip_large_mem_usage = True

    def write_observations(self, float_filelist, int_filelist):
        num_tracks = self.num_tracks

        # from Runner.set_tracknames()
        tracknames = [TRACKNAME_FMT % track_index
                      for track_index in xrange(num_tracks)]
        self.tracknames = tracknames
        self.tracknames_all = tracknames
        self.track_indexes = arange(len(tracknames))
        self.num_int_cols = num_tracks

        chunk_coords = [] # a "chunk" is what GMTK calls a segment
        num_bases = 0

        num_observations_list = []
        exponent_range = xrange(MAX_EXPONENT-1, MIN_EXPONENT-1, -1)
        for exponent in exponent_range:
            num_observations_array = arange(10, 1, -1, int) * 10**exponent
            num_observations_list += num_observations_array.tolist()

        for chunk_index, num_observations in enumerate(num_observations_list):
            chrom = CHROM_FMT % num_observations

            print >>sys.stderr, (num_tracks, num_observations)

            # make files
            float_filepath, int_filepath = \
                self.print_obs_filepaths(float_filelist, int_filelist, chrom,
                                         chunk_index)

            cells = float32(standard_normal((num_observations, num_tracks)))

            # XXX: refactor into accum_metadata_calc():
            # """recalculates metadata from real data"""
            row_shape = (num_tracks,)
            mins = cells.min(0)
            maxs = cells.max(0)
            sums = cells.sum(0)
            sums_squares = square(cells).sum(0)
            num_datapoints = fill_array(cells.shape[0], row_shape)
            self.accum_metadata(mins, maxs, sums, sums_squares, num_datapoints)

            self.save_observations_chunk(float_filepath, int_filepath, cells,
                                         None)

            num_bases += num_observations
            chunk_coords.append((chrom, 0, num_observations))

        self.num_chunks = chunk_index + 1
        self.num_bases = num_bases
        self.chunk_coords = chunk_coords

    def get_mem_per_obs(self, prog, num_tracks):
        # always return the largest number imaginable
        return MAX_MEM_PER_OBS[prog.prog]

    def make_job_name_res_usage(self, prog, chunk_name):
        return ".".join([make_job_name_stem_uuid(), prog.prog,
                         str(self.num_tracks), str(chunk_name)])

    def make_job_name_train(self, start_index, round_index, chunk_index):
        if chunk_index == NAME_BUNDLE_PLACEHOLDER:
            chunk_name = chunk_index
        else:
            chunk_name = self.chunk_lens[chunk_index]

        return self.make_job_name_res_usage(EM_TRAIN_PROG, chunk_name)

    def make_job_name_identify(self, prefix, chunk_index):
        prog = PREFIX2PROG[prefix]

        chunk_name = self.chunk_lens[chunk_index]

        return self.make_job_name_res_usage(prog, chunk_name)

    def gmtk_out2bed(self, *args, **kwargs):
        pass

    def posterior2wig(self, *args, **kwargs):
        pass

def run_res_usage():
    for num_tracks in xrange(MAX_NUM_TRACKS, 0, -1):
        runner = MemUsageRunner()
        runner.dirname = DIR_FMT % num_tracks
        runner.num_tracks = num_tracks
        runner.delete_existing = True

        runner()

def parse_sge_qacct(text):
    res = {}

    for line in text.rstrip().split("\n"):
        if line.startswith("="):
            if res:
                yield res
            continue

        key, space, val = line.partition(" ")
        res[key] = val.strip()

    yield res

def convert_sge_mem_size(text):
    try:
        multiplier = SGE_MEM_SIZE_SUFFIXES[text[-1]]
        significand = float(text[:-1])

        res = significand * multiplier
    except KeyError:
        res = float(text)

    return int(ceil(res))

def parse_res_usage(uuid):
    jobname = ".".join([make_job_name_stem(uuid), "*"])
    acct_text = QACCT_PROG.getoutput(j=jobname)

    # dict:
    # key: num_tracks
    # val: list of tuples of (mem_per_obs, cpu_per_obs)
    data = defaultdict(list)

    for record in parse_sge_qacct(acct_text):
        jobname = record["jobname"]
        jobname_words = jobname.split(".")

        program = jobname_words[1]
        num_tracks = int(jobname_words[2])
        num_observations = jobname_words[3] # this might also be "bundle"

        cpu = int(record["cpu"])
        maxvmem = convert_sge_mem_size(record["maxvmem"])

        if num_observations == NAME_BUNDLE_PLACEHOLDER:
            program = ".".join([program, NAME_BUNDLE_PLACEHOLDER])
            num_observations = 1 # do not divide
        else:
            num_observations = int(num_observations)

        mem_per_obs = maxvmem / num_observations
        cpu_per_obs = cpu / num_observations

        data[program, num_tracks].append((mem_per_obs, cpu_per_obs))

    writer = DictWriter(sys.stdout, FIELDNAMES)
    for (program, num_tracks), num_tracks_values in data.iteritems():
        mem_per_obs = int(ceil(max(num_tracks_values)[0]))
        cpu_per_obs = max(num_tracks_values, key=itemgetter(1))[1]

        writer.writerow(dict(program=program,
                             num_tracks=str(num_tracks),
                             island_base=ISLAND_BASE_NA, # means no island
                             island_lst=ISLAND_LST_NA,
                             mem_per_obs=mem_per_obs,
                             cpu_per_obs=cpu_per_obs))

def res_usage():
    run_res_usage()
    parse_res_usage(UUID)

def parse_options(args):
    from optparse import OptionParser

    usage = "%prog [OPTION]..."
    version = "%%prog %s" % __version__
    parser = OptionParser(usage=usage, version=version)

    options, args = parser.parse_args(args)

    if not len(args) == 0:
        parser.print_usage()
        sys.exit(1)

    return options, args

def main(args=sys.argv[1:]):
    options, args = parse_options(args)

    return res_usage(*args)

if __name__ == "__main__":
    sys.exit(main())
