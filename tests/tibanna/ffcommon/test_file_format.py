from tibanna_ffcommon.file_format import (
    FormatExtensionMap,
    parse_formatstr,
)
import pytest
import mock


@pytest.fixture
def minimal_format_search_result():
    return [{'file_format': 'bam',
             'standard_file_extension': 'bam',
             'extrafile_formats': ['/file-formats/bai/']},
             {'file_format': 'bai',
              'standard_file_extension': 'bam.bai'},
             {'file_format': 'fastq',
              'standard_file_extension': 'fastq.gz',
              'other_allowed_extensions': ['fq.gz']}
            ]

@pytest.fixture
def realistic_format_search_result():
    # a realistic search result but including only one two file formats, bam and bai
    return [{'principals_allowed': {'view': ['editor_for.12a92962-8265-4fc0-b2f8-cf14f05db58b',
                                             'group.admin', 'group.read-only-admin', 'remoteuser.EMBED', 'remoteuser.INDEXER'],
                                    'edit': ['editor_for.12a92962-8265-4fc0-b2f8-cf14f05db58b', 'group.admin']},
             'date_created': '2019-08-27T03:45:40.546949+00:00',
             '@type': ['FileFormat', 'Item'],
             'display_title': 'bam',
             'project': '/projects/cgap-core/',
             'description': 'This format is used for aligned reads',
             'submitted_by': '/users/986b362f-4eb6-4a9c-8173-3ab267221234/',
             'uuid': 'd13d06cf-218e-4f61-aaf0-91f226248b3c',
             'schema_version': '1',
             'extrafile_formats': ['/file-formats/bai/'],
             'institution': '/institutions/hms-dbmi/',
             'valid_item_types': ['FileProcessed'],
             'standard_file_extension': 'bam',
             '@id': '/file-formats/bam/',
             'last_modified': {'date_modified': '2019-11-05T20:18:08.793882+00:00',
                               'modified_by': '/users/986b362f-4eb6-4a9c-8173-3ab267221234/'},
             'file_format': 'bam',
             'status': 'in review'},
            {'principals_allowed': {'view': ['editor_for.12a92962-8265-4fc0-b2f8-cf14f05db58b',
                                             'group.admin', 'group.read-only-admin', 'remoteuser.EMBED', 'remoteuser.INDEXER'],
                                    'edit': ['editor_for.12a92962-8265-4fc0-b2f8-cf14f05db58b', 'group.admin']},
             'date_created': '2019-08-27T04:03:17.789281+00:00',
             '@type': ['FileFormat', 'Item'],
             'display_title': 'bai',
             'project': '/projects/cgap-core/',
             'description': 'Bam index format',
             'submitted_by': '/users/986b362f-4eb6-4a9c-8173-3ab267221234/',
             'uuid': 'd13d06c1-218e-4f61-aaf0-91f226248b3c',
             'schema_version': '1',
             'institution': '/institutions/hms-dbmi/',
             'valid_item_types': ['FileProcessed'],
             'standard_file_extension': 'bam.bai',
             '@id': '/file-formats/bai/',
             'last_modified': {'date_modified': '2019-11-05T20:18:08.890281+00:00',
                               'modified_by': '/users/986b362f-4eb6-4a9c-8173-3ab267221234/'},
             'file_format': 'bai',
             'status': 'in review'}]

def test_FormatExtensionMap(minimal_format_search_result):
    with mock.patch("tibanna_ffcommon.file_format.search_metadata", return_value=minimal_format_search_result):
        fe_map = FormatExtensionMap({'server': 'some_server'})
    assert hasattr(fe_map, 'fe_dict')
    assert fe_map.fe_dict == {'bam':{'standard_extension': 'bam',
                                     'other_allowed_extensions': [],
                                     'extrafile_formats': ['/file-formats/bai/']},
                              'bai':{'standard_extension': 'bam.bai',
                                     'extrafile_formats': [],
                                     'other_allowed_extensions': []},
                              'fastq':{'standard_extension': 'fastq.gz',
                                       'extrafile_formats': [],
                                       'other_allowed_extensions': ['fq.gz']}}
    assert fe_map.get_extension('bam') == 'bam'
    assert fe_map.get_extension('bai') == 'bam.bai'
    assert fe_map.get_other_extensions('fastq') == ['fq.gz']

def test_FormatExtensionMap2(realistic_format_search_result):
    with mock.patch("tibanna_ffcommon.file_format.search_metadata", return_value=realistic_format_search_result):
        fe_map = FormatExtensionMap({'server': 'some_server'})
    assert hasattr(fe_map, 'fe_dict')
    assert fe_map.fe_dict == {'bam':{'standard_extension': 'bam',
                                     'other_allowed_extensions': [],
                                     'extrafile_formats': ['/file-formats/bai/']},
                              'bai':{'standard_extension': 'bam.bai',
                                     'extrafile_formats': [],
                                     'other_allowed_extensions': []}}
    assert fe_map.get_extension('bam') == 'bam'
    assert fe_map.get_other_extensions('bai') == []
    assert fe_map.get_extension('fastq') is None

def test_parse_formatstr():
    assert parse_formatstr('bam') == 'bam'
    assert parse_formatstr('/file-formats/bai/') == 'bai'
    assert parse_formatstr('') is None
