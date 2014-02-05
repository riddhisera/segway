import sys
from os.path import basename
from array import array
from path import path
import cPickle as pickle
import struct
from distutils.spawn import find_executable
import subprocess
import pdb
import gzip
from numpy import array, log, float64, power, sum as npsum


from .virtual_evidence import write_virtual_evidence
from .bed import parse_bed4
from .observations import downsample_add
from ._util import (ceildiv, Copier, memoized_property,
                    VIRTUAL_EVIDENCE_FULL_LIST_FILENAME,
                    VIRTUAL_EVIDENCE_WINDOW_LIST_FILENAME_TMPL,
                    VIRTUAL_EVIDENCE_OBS_FILENAME_TMPL,
                    permissive_log, maybe_gzip_open)

SUBDIRNAME_MEAUSURE_PROP = "measure_prop"
MEASURE_PROP_WORKDIRNAME_TMPL = "mp.%s.%s_%s"
MEASURE_PROP_GRAPH_FILENAME = "graph.mp_graph"
MEASURE_PROP_TRANS_FILENAME = "trans.mp_trans"
MEASURE_PROP_LABEL_FILENAME = "label.mp_label"
MEASURE_PROP_POST_FILENAME = "post.mp_label"
MEASURE_PROP_OBJ_FILENAME = "objective.tab"
MEASURE_PROP_OUTPUT_FILENAME = "stdout.txt"

#MU = 10
#NU = 0

#################################################################
# Graph file
#################################################################

class MPGraphNode:
    def __init__(self):
        pass

    def init(self, index, neighbors):
        self.index = index
        # neighbors is a list of tuples (index, weight)
        self.neighbors = neighbors
        self.num_neighbors = len(neighbors)
        return self

    node_fmt = "IH"
    neighbor_fmt = "If"

    def write_to(self, f):
        f.write(struct.pack(MPGraphNode.node_fmt,
                            self.index, self.num_neighbors))
        for i in range(self.num_neighbors):
            f.write(struct.pack(MPGraphNode.neighbor_fmt,
                                *self.neighbors[i]))

    def read_from(self, f):
        self.index, self.num_neighbors = struct.unpack(MPGraphNode.node_fmt,
                                                       f.read(struct.calcsize(MPGraphNode.node_fmt)))
        self.neighbors = [None for i in range(self.num_neighbors)]
        for i in range(self.num_neighbors):
            self.neighbors[i] = struct.unpack(MPGraphNode.neighbor_fmt,
                                             f.read(struct.calcsize(MPGraphNode.neighbor_fmt)))
        return self

class MPGraph:
    def __init__(self):
        pass

    def init(self, nodes):
        self.nodes = nodes # nodes is a list of MPGraphNode's
        self.num_nodes = len(nodes)
        return self

    num_nodes_fmt = "I"

    def write_to(self, f):
        f.write(struct.pack(MPGraph.num_nodes_fmt, self.num_nodes))
        for i in range(self.num_nodes):
            self.nodes[i].write_to(f)

    def read_from(self, f):
        self.num_nodes, = struct.unpack(MPGraph.num_nodes_fmt,
                                       f.read(struct.calcsize(MPGraph.num_nodes_fmt)))

        self.nodes = [None for i in range(self.num_nodes)]
        for i in range(self.num_nodes):
            self.nodes[i] = MPGraphNode().read_from(f)
        return self

def test_graph():
    edge_weight = 1

    nodes = []
    for i in range(8):
        neighbors = []
        if (i != 0) and (i != 4):
            neighbors.append((i-1, edge_weight))
        if (i != 3) and (i != 7):
            neighbors.append((i+1, edge_weight))
        node = MPGraphNode().init(i, neighbors)
        nodes.append(node)
    graph = MPGraph().init(nodes)

    return graph
    pass

#################################################################
# Transduction file
#################################################################

class MPTransduction:
    def __init__(self):
        pass

    def init(self, labels):
        self.labels = labels
        return self

    label_fmt = "i"
    def write_to(self, f):
        for label in self.labels:
            f.write(struct.pack(MPTransduction.label_fmt, label))

    def read_from(self, f, num_nodes):
        self.labels = [None for i in range(num_nodes)]
        for i in range(num_nodes):
            self.labels[i], = struct.unpack(MPTransduction.label_fmt,
                                            f.read(struct.calcsize(MPTransduction.label_fmt)))
        return self

def test_transduction():
    labels = [1, 0, 0, -2, 1, 0, 0, -2]
    return MPTransduction().init(labels)

#################################################################
# Label file
#################################################################

class MPLabels:
    def __init__(self):
        pass

    def init(self, labels):
        self.labels = labels
        return self

    label_fmt = "i"
    def write_to(self, f):
        for i in range(len(self.labels)):
            f.write(struct.pack(MPLabels.label_fmt, self.labels[i]))

    def read_from(self, f, num_nodes):
        self.labels = [None for i in range(num_nodes)]
        for i in range(num_nodes):
            self.labels[i], = struct.unpack(MPLabels.label_fmt,
                                            f.read(struct.calcsize(MPLabels.label_fmt)))
        return self

def test_labels():
    labels = [0, 0, 0, 0, 1, 1, 1, 1]
    return MPLabels().init(labels)

#################################################################
# Measure-label file
#################################################################

class MPMeasureLabels:
    def __init__(self):
        pass

    def init(self, measure_labels):
        # format: list of probability distributions
        # where each dist is a list of floats
        self.measure_labels = measure_labels
        return self

    measure_label_fmt = "f"
    def write_to(self, f):
        for i in range(len(self.measure_labels)):
            for c in range(len(self.measure_labels[i])):
                f.write(struct.pack(MPMeasureLabels.measure_label_fmt, self.measure_labels[i][c]))

    def read_from(self, f, num_nodes, num_classes):
        self.labels = [[None for j in range(num_classes)] for i in range(num_nodes)]
        for i in range(num_nodes):
            self.labels[i], = struct.unpack(MPMeasureLabels.measure_label_fmt,
                                            f.read(struct.calcsize(MPMeasureLabels.measure_label_fmt)))
        return self

def test_measure_labels():
    measure_labels = [[.9,.1] for i in range(4)] + [[.1,.9] for i in range(4)]
    return MPMeasureLabels().init(measure_labels)

#################################################################
# MeasurePropRunner
#################################################################

class MeasurePropRunner(Copier):
    copy_attrs = ["windows", "resolution", "num_segs", "uniform_ve_dirname",
                  "work_dirpath", "num_worlds", "measure_prop_graph_filepath",
                  "mu", "mp_weight", "nu", "measure_prop_am_num_iters",
                  "measure_prop_reuse_evidence"]

    @memoized_property
    def num_frames(self):
        num_frames = 0
        for window_index, (world, chrom, start, end) in enumerate(self.windows):
            num_frames += ceildiv(end-start, self.resolution)
        return num_frames


    def __init__(self, runner):
        self.runner = runner
        self.posterior_filename = None
        Copier.__init__(self, runner)

    def make_mp_workdir(self, instance_index, round_index, mp_round_index):
        res = path(self.work_dirpath /
                   SUBDIRNAME_MEAUSURE_PROP /
                   MEASURE_PROP_WORKDIRNAME_TMPL % (instance_index, round_index, mp_round_index))
        if not res.isdir():
           res.makedirs()
        return res

    #def make_mp_graph_filename(self, instance_index, round_index):
        #return (self.make_mp_workdir(instance_index, round_index) /
                #MEASURE_PROP_GRAPH_FILENAME)

    def make_mp_trans_filename(self, instance_index, round_index, mp_round_index):
        return (self.make_mp_workdir(instance_index, round_index, mp_round_index) /
                MEASURE_PROP_TRANS_FILENAME)

    def make_mp_label_filename(self, instance_index, round_index, mp_round_index):
        return (self.make_mp_workdir(instance_index, round_index, mp_round_index) /
                MEASURE_PROP_LABEL_FILENAME)

    def make_mp_post_filename(self, instance_index, round_index, mp_round_index):
        return (self.make_mp_workdir(instance_index, round_index, mp_round_index) /
                MEASURE_PROP_POST_FILENAME)

    def make_mp_obj_filename(self, instance_index, round_index, mp_round_index):
        return (self.make_mp_workdir(instance_index, round_index, mp_round_index) /
                MEASURE_PROP_OBJ_FILENAME)

    def make_mp_output_filename(self, instance_index, round_index, mp_round_index):
        return (self.make_mp_workdir(instance_index, round_index, mp_round_index) /
                MEASURE_PROP_OUTPUT_FILENAME)

    def run_segway_posterior(self, instance_index, round_index, mp_round_index, params_filename):
        # need to specify: MP uniform ve files, structure file, params file

        round_index = "%s_%s" % (round_index, mp_round_index) # XXX

        if (not self.measure_prop_reuse_evidence) and (mp_round_index == 0):
            self.runner.measure_prop_ve_dirpath = self.uniform_ve_dirname

        posterior_workdir = \
                self.runner.make_mp_posterior_workdir(instance_index, round_index)
        self.posterior_tmpls = [(posterior_workdir /
                                 basename(self.runner.make_posterior_filename(window_index)))
                                for window_index in range(len(self.windows))]
        self.runner.run_identify_posterior_jobs(False, True,
                                                [], self.posterior_tmpls,
                                                params_filename,
                                                instance_index, round_index,
                                                mp_round_index=mp_round_index)
        self.runner.measure_prop_ve_dirpath = \
            self.runner.make_mp_posterior_workdir(instance_index, round_index)

    def write_mp_trans_file(self, instance_index, round_index, mp_round_index):
        print >>sys.stderr, "Using low-memory write_mp_trans_file"
        filepath = self.make_mp_trans_filename(instance_index, round_index, mp_round_index)
        label_fmt = "i"
        with open(filepath, "w") as f:
            for i in range(self.num_frames):
                f.write(struct.pack(label_fmt, 1))

    def write_mp_label_file(self, instance_index, round_index, mp_round_index):
        print >>sys.stderr, "Using low-memory write_mp_label_file."
        filepath = self.make_mp_label_filename(instance_index, round_index, mp_round_index)

        with open(filepath, "w") as f:
            # read posterior files from self.posterior_tmpls
            #window_posteriors = [None for window_index in range(len(self.windows))]
            for window_index, (window_world, window_chrom, window_start, window_end) \
                    in enumerate(self.windows):
                #print >>sys.stderr, "window_index:", window_index
                post_tmpl = self.posterior_tmpls[window_index]

                # read segway posterior for this window
                # (initialize to 10 so that if any posteriors don't get assignments,
                # they should violate the distribution constraint)
                window_num_frames = ceildiv(window_end - window_start, self.resolution)
                posteriors = [[10 for i in range(self.num_segs)] for j in range(window_num_frames)]
                for label_index in range(self.num_segs):
                    post_fname = post_tmpl % label_index
                    with maybe_gzip_open(post_fname, "r") as post:
                        for line in post:
                            row, (chrom, start, end, prob) = parse_bed4(line)
                            start = int(start)
                            end = int(end)
                            prob = float(prob) / 100

                            try:
                                assert chrom == window_chrom
                                assert start >= window_start
                                assert end <= window_end
                            except:
                                pdb.set_trace()

                            # segway's posteriors should line up with the resolution
                            try:
                                assert ((end - start) % self.resolution) == 0
                                assert ((start - window_start) % self.resolution) == 0
                            except:
                                pdb.set_trace()
                            num_obs = ceildiv(end - start, self.resolution)
                            first_obs_index = (start - window_start) / self.resolution
                            for obs_index in range(first_obs_index, first_obs_index+num_obs):
                                posteriors[obs_index][label_index] = prob

                # add psuedocounts to avoid breaking measure prop
                for frame_index in range(window_num_frames):
                    posteriors[frame_index] = [((posteriors[frame_index][i] + 1e-20) /
                                               (1 + 1e-20*self.num_segs))
                                               for i in range(len(posteriors[frame_index]))]

                # assert distribution constraint
                assert len(posteriors[frame_index]) == self.num_segs
                for frame_index in range(window_num_frames):
                    try:
                        assert (abs(sum(posteriors[frame_index]) - 1) < 0.01)
                    except:
                        print posteriors[frame_index]
                        raise

                measure_label_fmt = "%sf" % self.num_segs
                for i in range(len(posteriors)):
                    f.write(struct.pack(measure_label_fmt, *posteriors[i]))

                #window_posteriors[window_index] = posteriors

            #mp_labels = MPMeasureLabels().init(labels)
                #mp_labels.write_to(f)

    def run_measure_prop(self, instance_index, round_index, mp_round_index):
        mp_exe = find_executable("MP_large_scale")
        if mp_exe is None:
            raise Exception("Could not find MP_large_scale executable!")
        #graph_filepath = self.make_mp_graph_filename(instance_index, round_index)
        graph_filepath = self.measure_prop_graph_filepath
        trans_filepath = self.make_mp_trans_filename(instance_index, round_index, mp_round_index)
        label_filepath = self.make_mp_label_filename(instance_index, round_index, mp_round_index)
        post_filepath = self.make_mp_post_filename(instance_index, round_index, mp_round_index)
        obj_filepath = self.make_mp_obj_filename(instance_index, round_index, mp_round_index)
        mp_output_filepath = self.make_mp_output_filename(instance_index, round_index, mp_round_index)
        cmd = [mp_exe,
               "-inputGraphName", graph_filepath,
               "-transductionFile", trans_filepath,
               "-labelFile", label_filepath,
               "-numThreads", "32",
               "-outPosteriorFile", post_filepath,
               "-numClasses", str(self.num_segs),
               "-mu", str(self.mu),
               "-nu", str(self.nu),
               "-nWinSize", "1",
               "-printAccuracy", "false",
               "-measureLabels", "true",
               "-maxIters", str(self.measure_prop_am_num_iters),
               "-outObjFile", obj_filepath]
        print >>sys.stderr, "MP command:"
        print >>sys.stderr, " ".join(cmd)
        #with open(mp_output_filepath, "w") as mp_output:
            #subprocess.check_call(cmd, stderr=subprocess.STDOUT, stdout=mp_output)
        subprocess.check_call(cmd, stderr=subprocess.STDOUT, stdout=sys.stderr)

    # XXX duplicative of mp_post_to_ve, write_virtual_evidence, read_mp_post_file
    def mp_post_to_ve_lowmem(self, instance_index, round_index, mp_round_index):
        print >>sys.stderr, "Using  mp_post_to_ve_lowmem"
        ve_dirname = path(self.runner.measure_prop_ve_dirpath)

        header_fmt = "IH"
        mp_post_filepath = self.make_mp_post_filename(instance_index, round_index, mp_round_index)

        frame_fmt = "%sf" % self.num_segs
        with open(mp_post_filepath, "r") as f:
            num_nodes, num_classes = struct.unpack(header_fmt,
                                                   f.read(struct.calcsize(header_fmt)))
            assert (num_classes == self.num_segs)
            assert (num_nodes == self.num_frames)
            node_fmt = "I%sf" % self.num_segs

            for window_index, (world, chrom, start, end) in enumerate(self.windows):
                #print >>sys.stderr, "window_index:", window_index
                window_posts = []
                window_num_frames = ceildiv(end-start, self.resolution)
                for i in range(window_num_frames):
                    # Read MP posteriors from f
                    line = struct.unpack(node_fmt,
                                         f.read(struct.calcsize(node_fmt)))
                    index = line[0]
                    post = array(line[1:], dtype=float64)

                    # Transform posterior with mp_weight parameter, normalize and take log
                    post = power(post, self.mp_weight / (1.0 + self.mp_weight)) + 1e-250
                    #post = map(lambda p: p**self.mp_weight, post)
                    #partition = sum(post)
                    #post = map(lambda p: float(p) / partition, post)
                    post = log(post / npsum(post))
                    #post = map(permissive_log, post)

                    window_posts.append(post)

                # write observations
                obs_filename = (ve_dirname / VIRTUAL_EVIDENCE_OBS_FILENAME_TMPL % window_index)
                if not path(obs_filename).isfile():
                    with open(obs_filename, "w") as obs_file:
                        for frame_index, obs in enumerate(window_posts):
                            assert (len(obs) == self.num_segs)
                            obs_file.write(struct.pack(frame_fmt, *obs))

        # Write other virtual evidence files
        obs_filenames = [(ve_dirname /
                          VIRTUAL_EVIDENCE_OBS_FILENAME_TMPL % window_index)
                         for window_index in range(len(self.windows))]


        full_list_filename = ve_dirname / VIRTUAL_EVIDENCE_FULL_LIST_FILENAME
        window_list_filenames = [(ve_dirname /
                                  VIRTUAL_EVIDENCE_WINDOW_LIST_FILENAME_TMPL % window_index)
                                 for window_index in range(len(self.windows))]

        # write full list
        with open(full_list_filename, "w") as list_file:
            list_file.write("\n".join(obs_filenames))

        # write window lists
        for window_index in range(len(self.windows)):
            window_list_filename = window_list_filenames[window_index]
            obs_filename = obs_filenames[window_index]
            with open(window_list_filename, "w") as window_list_file:
                window_list_file.write(obs_filename)









    def load(self, instance_index):
        # make uniform VE files
        #def make_obs_iter():
            #ve_line = [log(float(1)/(self.num_segs)) for i in range(self.num_segs)]
            #for window_index, (world, chrom, start, end) in enumerate(self.windows):
                #num_frames = ceildiv(end-start, self.resolution)
                #yield (ve_line for frame_index in range(num_frames))

        #write_virtual_evidence(make_obs_iter(),
                               #self.uniform_ve_dirname,
                               #self.windows,
                               #self.num_segs)

        self.runner.measure_prop_ve_dirpath = self.uniform_ve_dirname


    def update(self, instance_index, round_index, mp_round_index, params_filename=None):
        # 1) Run gmtkJT to get posteriors for the current model
        # This runs gmtkJT and puts the posteriors at posterior_filenames
        self.run_segway_posterior(instance_index, round_index, mp_round_index, params_filename)
        #pickle.dump(self, open(path(self.work_dirpath) / "mp.pckl", "w"))

        # 2) convert gmtkJT posteriors to MP label format
        # (the filenames are read from self.posterior_tmpls)
        self.write_mp_label_file(instance_index, round_index, mp_round_index)

        # 3) write MP graph, trans files
        #self.write_mp_graph_file(instance_index, round_index)
        self.write_mp_trans_file(instance_index, round_index, mp_round_index)

        # 4) run MP
        self.run_measure_prop(instance_index, round_index, mp_round_index)

        # 5) convert MP posteriors to VE
        self.mp_post_to_ve_lowmem(instance_index, round_index, mp_round_index)




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('runner_fname')
    parser.add_argument('mp_fname')
    args = parser.parse_args()

    runner = Runner()
    mp = pickle.load(open(args.mp_fname, "r"))



