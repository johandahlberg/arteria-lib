import unittest

from bcl2fastq.lib.bcl2fastq_utils import *
from test_utils import TestUtils

class TestBcl2FastqConfig(unittest.TestCase):

    test_dir = os.path.dirname(os.path.realpath(__file__))
    samplesheet_file = test_dir + "/sampledata/samplesheet_example.csv"

    def test_get_bcl2fastq_version_from_run_parameters(self):
        runfolder = TestBcl2FastqConfig.test_dir + "/sampledata/HiSeq-samples/2014-02_13_average_run"
        version = Bcl2FastqConfig.get_bcl2fastq_version_from_run_parameters(runfolder, TestUtils.DUMMY_CONFIG)
        self.assertEqual(version, "1.8.4")

    def test_get_length_of_indexes(self):
        runfolder = TestBcl2FastqConfig.test_dir + "/sampledata/HiSeq-samples/2014-02_13_average_run"
        index_and_length = Bcl2FastqConfig.get_length_of_indexes(runfolder)
        self.assertEqual(index_and_length, {2: 7})

    def test_get_bases_mask_per_lane_from_samplesheet(self):
        #TODO Fix test to match that we might now have a read that uses the full
        # lenght of the read.
        mock_read_index_lengths = {1: 9, 2: 9}
        expected_bases_mask = {1: "y*,8in*,8in*,y*",
                               2: "y*,6in*,n*,y*",
                               3: "y*,6in*,n*,y*",
                               4: "y*,7in*,n*,y*",
                               5: "y*,7in*,n*,y*",
                               6: "y*,7in*,n*,y*",
                               7: "y*,7in*,n*,y*",
                               8: "y*,7in*,n*,y*",
                               }
        actual_bases_mask = Bcl2FastqConfig.\
            get_bases_mask_per_lane_from_samplesheet(TestBcl2FastqConfig.samplesheet_file, mock_read_index_lengths)
        self.assertEqual(expected_bases_mask, actual_bases_mask)

    def test_get_bases_mask_per_lane_from_samplesheet_invalid_length_combo(self):
        # These are to short compared to the length indicated in the samplesheet
        mock_read_index_lengths = {1: 4, 2: 4}

        with self.assertRaises(AssertionError):
            Bcl2FastqConfig.\
                get_bases_mask_per_lane_from_samplesheet(TestBcl2FastqConfig.samplesheet_file, mock_read_index_lengths)


class TestBCL2FastqRunnerFactory(unittest.TestCase):

    def test_create_bcl2fastq1x_runner(self):
        config = Bcl2FastqConfig(bcl2fastq_version = "1.8.4",
                                 runfolder_input = "test/runfolder",
                                 output = "test/output")

        factory = BCL2FastqRunnerFactory(TestUtils.DUMMY_CONFIG)
        runner = factory.create_bcl2fastq_runner(config)
        self.assertIsInstance(runner, BCL2Fastq1xRunner)

    def test_create_bcl2fastq2x_runner(self):
        config = Bcl2FastqConfig(bcl2fastq_version = "2.15.2",
                                 runfolder_input = "test/runfolder",
                                 output = "test/output")

        factory = BCL2FastqRunnerFactory(TestUtils.DUMMY_CONFIG)
        runner = factory.create_bcl2fastq_runner(config)
        self.assertIsInstance(runner, BCL2Fastq2xRunner, msg= "runner is: " + str(runner))

    def test_create_invalid_version_runner(self):
        config = Bcl2FastqConfig(bcl2fastq_version = "1.7",
                                 runfolder_input = "test/runfolder",
                                 output = "test/output")

        factory = BCL2FastqRunnerFactory(TestUtils.DUMMY_CONFIG)
        with self.assertRaises(LookupError):
            factory.create_bcl2fastq_runner(config)


class TestBCL2Fastq2xRunner(unittest.TestCase):
    def test_construct_command(self):

        config = Bcl2FastqConfig(
            bcl2fastq_version = "2.15.2",
            runfolder_input = "test/runfolder",
            output = "test/output",
            barcode_mismatches = "2",
            tiles="s1,s2,s3",
            use_base_mask="Y*NN",
            additional_args="--my-best-arg 1 --my-best-arg 2")

        runner = BCL2Fastq2xRunner(config, "/bcl/binary/path")
        command = runner.construct_command()
        expected_command = "/bcl/binary/path --input-dir test/runfolder/Data/Intensities/BaseCalls " \
                           "--output-dir test/output --barcode-mismatches 2 " \
                           "--tiles s1,s2,s3 --use_base_mask Y*NN " \
                           "--my-best-arg 1 --my-best-arg 2"
        self.assertEqual(command, expected_command)


class TestBCL2FastqRunner(unittest.TestCase):

    class DummyBCL2FastqRunner(BCL2FastqRunner):
        def __init__(self, config, binary, dummy_command):
            self.dummy_command = dummy_command
            BCL2FastqRunner.__init__(self, config, binary)

        def construct_command(self):
            return self.dummy_command

    def test__successful_run(self):

        dummy_runner = self.DummyBCL2FastqRunner(None, None, "echo 'high tech low life'; exit 0")
        success = dummy_runner.run()
        self.assertTrue(success)

    def test__unsuccessful_run(self):

        dummy_runner = self.DummyBCL2FastqRunner(None, None,  "echo 'high tech low life'; exit 1")
        success = dummy_runner.run()
        self.assertFalse(success)

class TestBCL2Fastq1xRunner(unittest.TestCase):

    def test_construct_command(self):
        config = Bcl2FastqConfig(
            bcl2fastq_version = "1.8.4",
            runfolder_input = "test/runfolder",
            output = "test/output",
            barcode_mismatches = "2",
            tiles="s1,s2,s3",
            use_base_mask="Y*NN",
            additional_args="--my-best-arg 1 --my-best-arg 2")

        runner_1 = BCL2Fastq1xRunner(config, "/dummy/binary")
        command = runner_1.construct_command()
        expected_command = "configureBclToFastq.pl " \
                           "--input-dir test/runfolder/Data/Intensities/BaseCalls " \
                           "--sample-sheet test/runfolder/Samplesheet.csv " \
                           "--output-dir test/output " \
                           "--fastq-cluster-count 0 " \
                           "--force " \
                           "--mismatches 2 " \
                           "--tiles s1,s2,s3 " \
                           "--use_bases_mask Y*NN " \
                           "--my-best-arg 1 " \
                           "--my-best-arg 2  " \
                           "&& make -j{0}".format(config.nbr_of_cores)

        self.assertEqual(command, expected_command)
