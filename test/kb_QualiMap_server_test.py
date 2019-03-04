# -*- coding: utf-8 -*-
import os
import shutil
import time
import unittest
from configparser import ConfigParser  # py3
from os import environ
from pprint import pprint
from unittest.mock import patch

from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.GenomeFileUtilClient import GenomeFileUtil
from installed_clients.ReadsAlignmentUtilsClient import ReadsAlignmentUtils
from installed_clients.ReadsUtilsClient import ReadsUtils
from installed_clients.SetAPIServiceClient import SetAPI
from installed_clients.WorkspaceClient import Workspace
from kb_QualiMap.QualiMapRunner import QualiMapRunner
from kb_QualiMap.authclient import KBaseAuth as _KBaseAuth
from kb_QualiMap.kb_QualiMapImpl import kb_QualiMap
from kb_QualiMap.kb_QualiMapServer import MethodContext


class kb_QualiMapTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        token = environ.get('KB_AUTH_TOKEN', None)
        config_file = environ.get('KB_DEPLOYMENT_CONFIG', None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items('kb_QualiMap'):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg['auth-service-url']
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update({'token': token,
                        'user_id': user_id,
                        'provenance': [
                            {'service': 'kb_QualiMap',
                             'method': 'please_never_use_it_in_production',
                             'method_params': []
                             }],
                        'authenticated': 1})
        cls.wsURL = cls.cfg['workspace-url']
        cls.ws = Workspace(cls.wsURL)
        cls.serviceImpl = kb_QualiMap(cls.cfg)
        cls.scratch = cls.cfg['scratch']
        cls.srv_wiz_url = cls.cfg['srv-wiz-url']
        cls.callback_url = os.environ['SDK_CALLBACK_URL']

        cls.gfu = GenomeFileUtil(cls.callback_url)
        cls.dfu = DataFileUtil(cls.callback_url)
        cls.ru = ReadsUtils(cls.callback_url)
        cls.rau = ReadsAlignmentUtils(cls.callback_url)
        cls.au = AssemblyUtil(cls.callback_url)

        suffix = int(time.time() * 1000)
        cls.wsName = "test_kb_qualimap_" + str(suffix)
        cls.ws.create_workspace({'workspace': cls.wsName})

        cls.prepare_data()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'wsName'):
            cls.ws.delete_workspace({'workspace': cls.wsName})
            print('Test workspace ' + cls.wsName + ' was deleted')

    @classmethod
    def prepare_data(cls):

        workspace_id = cls.dfu.ws_name_to_id(cls.wsName)

        # upload genome object
        genbank_file_name = 'minimal.gbff'
        genbank_file_path = os.path.join(cls.scratch, genbank_file_name)
        shutil.copy(os.path.join('data', genbank_file_name), genbank_file_path)

        genome_object_name = 'test_Genome'
        cls.genome_ref = cls.gfu.genbank_to_genome({'file': {'path': genbank_file_path},
                                                    'workspace_name': cls.wsName,
                                                    'genome_name': genome_object_name
                                                    })['genome_ref']
        print('TEST genome_ref=' + cls.genome_ref)

        # upload assembly object
        file_name = 'test.fna'
        fasta_path = os.path.join(cls.scratch, file_name)
        shutil.copy(os.path.join('data', file_name), fasta_path)
        assembly_name = 'test_assembly'
        cls.assembly_ref = cls.au.save_assembly_from_fasta({'file': {'path': fasta_path},
                                                            'workspace_name': cls.wsName,
                                                            'assembly_name': assembly_name})

        print('TEST assembly_ref=' + cls.assembly_ref)

        # upload reads object
        reads_file_name = 'Sample1.fastq'
        reads_file_path = os.path.join(cls.scratch, reads_file_name)
        shutil.copy(os.path.join('data', reads_file_name), reads_file_path)

        reads_object_name_1 = 'test_Reads_1'
        cls.reads_ref_1 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                               'wsname': cls.wsName,
                                               'sequencing_tech': 'Unknown',
                                               'interleaved': 0,
                                               'name': reads_object_name_1
                                               })['obj_ref']
        print(('TEST reads_ref_1=' + cls.reads_ref_1))

        reads_object_name_2 = 'test_Reads_2'
        cls.reads_ref_2 = cls.ru.upload_reads({'fwd_file': reads_file_path,
                                               'wsname': cls.wsName,
                                               'sequencing_tech': 'Unknown',
                                               'interleaved': 0,
                                               'name': reads_object_name_2
                                               })['obj_ref']
        print('TEST reads_ref_2=' + cls.reads_ref_2)

        # upload alignment object
        alignment_file_name = 'accepted_hits.bam'
        alignment_file_path = os.path.join(cls.scratch, alignment_file_name)
        shutil.copy(os.path.join('data', alignment_file_name), alignment_file_path)

        alignment_object_name_1 = 'test_Alignment_1'
        cls.condition_1 = 'test_condition_1'
        cls.alignment_ref_1 = cls.rau.upload_alignment(
                                   {'file_path': alignment_file_path,
                                    'destination_ref': cls.wsName + '/' + alignment_object_name_1,
                                    'read_library_ref': cls.reads_ref_1,
                                    'condition':  cls.condition_1,
                                    'library_type': 'single_end',
                                    'assembly_or_genome_ref': cls.genome_ref
                                    })['obj_ref']
        print('TEST alignment_ref_1=' + cls.alignment_ref_1)

        alignment_object_name_2 = 'test_Alignment_2'
        cls.condition_2 = 'test_condition_2'
        cls.alignment_ref_2 = cls.rau.upload_alignment(
                                   {'file_path': alignment_file_path,
                                    'destination_ref': cls.wsName + '/' + alignment_object_name_2,
                                    'read_library_ref': cls.reads_ref_2,
                                    'condition':  cls.condition_2,
                                    'library_type': 'single_end',
                                    'assembly_or_genome_ref': cls.genome_ref
                                    })['obj_ref']
        print('TEST alignment_ref_2=' + cls.alignment_ref_2)

        alignment_object_name_3 = 'test_Alignment_3'
        cls.condition_3 = 'test_condition_3'
        cls.alignment_ref_3 = cls.rau.upload_alignment(
                                   {'file_path': alignment_file_path,
                                    'destination_ref': cls.wsName + '/' + alignment_object_name_3,
                                    'read_library_ref': cls.reads_ref_2,
                                    'condition':  cls.condition_3,
                                    'library_type': 'single_end',
                                    'assembly_or_genome_ref': cls.assembly_ref
                                    })['obj_ref']
        print('TEST alignment_ref_3=' + cls.alignment_ref_3)

        # upload sample_set object

        sample_set_object_name = 'test_Sample_Set'
        sample_set_data = {
                    'sampleset_id': sample_set_object_name,
                    'sample_ids': [cls.reads_ref_1, cls.reads_ref_2],
                    'sampleset_desc': 'test sampleset object',
                    'Library_type': 'SingleEnd',
                    'condition': [cls.condition_1, cls.condition_2],
                    'domain': 'Unknown',
                    'num_samples': 2,
                    'platform': 'Unknown'}
        save_object_params = {
            'id': workspace_id,
            'objects': [{
                            'type': 'KBaseRNASeq.RNASeqSampleSet',
                            'data': sample_set_data,
                            'name': sample_set_object_name
                        }]
        }

        dfu_oi = cls.dfu.save_objects(save_object_params)[0]
        cls.sample_set_ref = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])
        print(('TEST sample_set_ref=' + cls.sample_set_ref))

        # upload alignment_set object
        object_type = 'KBaseRNASeq.RNASeqAlignmentSet'
        alignment_set_object_name = 'test_Alignment_Set'
        alignment_set_data = {
                    'genome_id': cls.genome_ref,
                    'read_sample_ids': [reads_object_name_1, reads_object_name_2],
                    'mapped_rnaseq_alignments': [{reads_object_name_1: alignment_object_name_1},
                                                 {reads_object_name_2: alignment_object_name_2}],
                    'mapped_alignments_ids': [{reads_object_name_1: cls.alignment_ref_1},
                                              {reads_object_name_2: cls.alignment_ref_2}],
                    'sample_alignments': [cls.alignment_ref_1, cls.alignment_ref_2],
                    'sampleset_id': cls.sample_set_ref}
        save_object_params = {
            'id': workspace_id,
            'objects': [{
                            'type': object_type,
                            'data': alignment_set_data,
                            'name': alignment_set_object_name
                        }]
        }

        dfu_oi = cls.dfu.save_objects(save_object_params)[0]
        cls.old_alignment_set_ref = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])
        print('TEST (legacy) KBaseRNASeq.alignment_set_ref=' + cls.old_alignment_set_ref)

        # Save the alignment set
        items = [{'ref': cls.alignment_ref_1, 'label': 'c1'}, {'ref': cls.alignment_ref_2, 'label': 'c2'}]
        alignment_set_data = {'description': '', 'items': items}
        alignment_set_save_params = {'data': alignment_set_data,
                                     'workspace': cls.wsName,
                                     'output_object_name': 'MyReadsAlignmentSet'}

        set_api = SetAPI(cls.srv_wiz_url)
        save_result = set_api.save_reads_alignment_set_v1(alignment_set_save_params)
        cls.new_alignment_set_ref = save_result['set_ref']
        print('TEST KBaseSet.alignment_set_ref=')
        print(cls.new_alignment_set_ref)

    def getWsClient(self):
        return self.__class__.wsClient

    def getWsName(self):
        return self.__class__.wsName

    def getImpl(self):
        return self.__class__.serviceImpl

    def getContext(self):
        return self.__class__.ctx

    def test_single(self):
        params = {
            'input_ref': self.alignment_ref_1,
            'create_report': 1,
            'output_workspace': self.getWsName()
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)

    def test_single_with_assembly(self):
        params = {
            'input_ref': self.alignment_ref_3,
            'create_report': 1,
            'output_workspace': self.getWsName()
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)

    def run_bamqc_failure(input_ref, input_info):
        raise ValueError('run_bamqc failed')

    @patch.object(QualiMapRunner, "run_bamqc", side_effect=run_bamqc_failure)
    def test_single_failure(self, run_bamqc):
        params = {
            'input_ref': self.alignment_ref_1,
            'create_report': 1,
            'output_workspace': self.getWsName()
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)

    @patch.object(QualiMapRunner, "LARGE_BAM_FILE_SIZE", new=1)
    def test_single_large_file(self):
        params = {
            'input_ref': self.alignment_ref_1,
            'create_report': 1,
            'output_workspace': self.getWsName()
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        # really no good way to assert in large file case
        # just serach 'Running:' and see if the command has '--java-mem-size=4G'
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)

    @patch.object(QualiMapRunner, "TIMEOUT", new=1)
    def test_single_file_timeout(self):
        params = {
            'input_ref': self.alignment_ref_1,
            'create_report': 1,
            'output_workspace': self.getWsName()
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)

    def test_multi_no_report(self):
        params = {
            'input_ref': self.new_alignment_set_ref
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertNotIn('report_name', result)
        self.assertNotIn('report_ref', result)

    def test_multi(self):
        params = {
            'input_ref': self.new_alignment_set_ref,
            'create_report': 1,
            'output_workspace': self.getWsName()
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)

    def run_multi_sample_qc_failure(input_ref, input_info):
        raise ValueError('run_multi_sample_qc failed')

    @patch.object(QualiMapRunner, "run_multi_sample_qc", side_effect=run_multi_sample_qc_failure)
    def test_multi_failure(self, run_multi_sample_qc):
        params = {
            'input_ref': self.new_alignment_set_ref,
            'create_report': 1,
            'output_workspace': self.getWsName()
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)

    @patch.object(QualiMapRunner, "LARGE_BAM_FILE_SIZE", new=1)
    def test_multi_large_file(self):
        params = {
            'input_ref': self.new_alignment_set_ref,
            'create_report': 1,
            'output_workspace': self.getWsName()
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        # really no good way to assert in large file case
        # just serach 'Running:' and see if the command has '--java-mem-size=4G'
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)

    @patch.object(QualiMapRunner, "TIMEOUT", new=1)
    def test_multi_timeout(self):
        params = {
            'input_ref': self.new_alignment_set_ref,
            'create_report': 1,
            'output_workspace': self.getWsName()
        }
        result = self.getImpl().run_bamqc(self.getContext(), params)[0]
        pprint(result)
        self.assertIn('qc_result_folder_path', result)
        self.assertIn('qc_result_zip_info', result)
        self.assertIn('shock_id', result['qc_result_zip_info'])
        self.assertIn('report_name', result)
        self.assertIn('report_ref', result)
