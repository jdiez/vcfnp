"""
Some simple unit tests for the vcfnp extension.

"""


from vcfnp import variants, calldata, EFF_DEFAULT_DTYPE, eff_default_transformer
from nose.tools import eq_, assert_almost_equal
import re
import numpy as np


def test_variants():
    a = variants('fixture/sample.vcf', arities={'ALT': 2, 'AC': 2})
    print repr(a)
    eq_(9, len(a))

    eq_('19', a[0]['CHROM'])
    eq_(111, a[0]['POS'])
    eq_('rs6054257', a[2]['ID'])
    eq_('A', a[0]['REF'])
    eq_('ATG', a[8]['ALT'][1])
    eq_(10.0, a[1]['QUAL'])
    eq_(True, a[2]['FILTER']['PASS'])
    eq_(False, a[3]['FILTER']['PASS'])
    eq_(True, a[3]['FILTER']['q10'])
    eq_(2, a[0]['num_alleles'])
    eq_(False, a[5]['is_snp'])

    # INFO fields
    eq_(3, a[2]['NS'])
    eq_(.5, a[2]['AF'])
    eq_(True, a[2]['DB'])
    eq_((3, 1), tuple(a[6]['AC']))


def test_variants_flatten_filter():
    a = variants('fixture/sample.vcf', flatten_filter=True)
    eq_(True, a[2]['FILTER_PASS'])
    eq_(False, a[3]['FILTER_PASS'])
    eq_(True, a[3]['FILTER_q10'])


def test_variants_region():
    a = variants('fixture/sample.vcf.gz', region='20')
    eq_(6, len(a))
    
    
def test_variants_region_empty():
    a = variants('fixture/sample.vcf.gz', region='18')
    eq_(0, len(a))
    a = variants('fixture/sample.vcf.gz', region='19:113-200')
    eq_(0, len(a))


def test_variants_count():
    a = variants('fixture/sample.vcf', count=3)
    eq_(3, len(a))
    
    
def test_variants_exclude_fields():
    a = variants('fixture/sample.vcf', exclude_fields=['ID', 'FILTER'])
    assert 'CHROM' in a.dtype.names
    assert 'ID' not in a.dtype.names
    assert 'FILTER' not in a.dtype.names
    
    
def test_variants_slice():
    a = variants('fixture/sample.vcf.gz')
    eq_('rs6054257', a['ID'][2])
    a = variants('fixture/sample.vcf.gz', slice=(0, None, 2))
    eq_('rs6054257', a['ID'][1])
    
    
def test_calldata():
    a = calldata('fixture/sample.vcf')
    print repr(a)
    eq_('0|0', a[0]['NA00001']['GT'])
    eq_(True, a[0]['NA00001']['is_called'])
    eq_(True, a[0]['NA00001']['is_phased'])
    eq_((0, 0), tuple(a[0]['NA00001']['genotype']))
    eq_((-1, -1), tuple(a[6]['NA00003']['genotype']))
    eq_((-1, -1), tuple(a[7]['NA00003']['genotype']))
    eq_((10, 10), tuple(a[0]['NA00001']['HQ']))

#>>> a['NA00001']
#array([(True, True, [0, 0], '0|0', 0, 0, [10, 10]),
#       (True, True, [0, 0], '0|0', 0, 0, [10, 10]),
#       (True, True, [0, 0], '0|0', 48, 1, [51, 51]),
#       (True, True, [0, 0], '0|0', 49, 3, [58, 50]),
#       (True, True, [1, 2], '1|2', 21, 6, [23, 27]),
#       (True, True, [0, 0], '0|0', 54, 0, [56, 60]),
#       (True, False, [0, 1], '0/1', 0, 4, [0, 0]),
#       (True, False, [0, 0], '0/0', 0, 0, [0, 0]),
#       (True, False, [0, -1], '0', 0, 0, [0, 0])], 
#      dtype=[('is_called', '|b1'), ('is_phased', '|b1'), ('genotype', '|i1', (2,)), ('GT', '|S3'), ('GQ', '|u1'), ('DP', '<u2'), ('HQ', '<i4', (2,))])


def test_calldata_region():
    a = calldata('fixture/sample.vcf.gz', region='20')
    eq_(6, len(a))


def test_calldata_region_empty():
    a = calldata('fixture/sample.vcf.gz', region='18')
    eq_(0, len(a))
    a = calldata('fixture/sample.vcf.gz', region='19:113-200')
    eq_(0, len(a))


def test_condition():
    V = variants('fixture/sample.vcf')
    eq_(9, len(V))
    C = calldata('fixture/sample.vcf', condition=V['FILTER']['PASS'])
    eq_(5, len(C))
    Vf = variants('fixture/sample.vcf', condition=V['FILTER']['PASS'])
    eq_(5, len(Vf))
    

def test_variable_calldata():
    C = calldata('fixture/test1.vcf')
    eq_((1, 0), tuple(C['test2']['AD'][0]))
    eq_((1, 0), tuple(C['test2']['AD'][1]))
    eq_((1, 0), tuple(C['test2']['AD'][2]))
    eq_('.', C['test2']['GT'][0])
    eq_('0', C['test2']['GT'][1])
    eq_('1', C['test2']['GT'][2])
    
    
def test_missing_calldata():
    C = calldata('fixture/test1.vcf')
    eq_('.', C['test3']['GT'][2])
    eq_((-1, -1), tuple(C['test3']['genotype'][2]))
    eq_('./.', C['test4']['GT'][2])
    eq_((-1, -1), tuple(C['test4']['genotype'][2]))


def test_override_vcf_types():
    V = variants('fixture/test4.vcf')
    eq_(0, V['MQ0Fraction'][2])
    V = variants('fixture/test4.vcf', vcf_types={'MQ0Fraction': 'Float'})
    assert_almost_equal(0.03, V['MQ0Fraction'][2])


def test_variants_transformers():
    V = variants('fixture/test12.vcf',
                 dtypes={'EFF': EFF_DEFAULT_DTYPE},
                 arities={'EFF': 1},
                 transformers={'EFF': eff_default_transformer()})

    eq_('STOP_GAINED', V['EFF']['Effect'][0])
    eq_('HIGH', V['EFF']['Effect_Impact'][0])
    eq_('NONSENSE', V['EFF']['Functional_Class'][0])
    eq_('Cag/Tag', V['EFF']['Codon_Change'][0])
    eq_('Q236*', V['EFF']['Amino_Acid_Change'][0])
    eq_(749, V['EFF']['Amino_Acid_Length'][0])
    eq_('NOC2L', V['EFF']['Gene_Name'][0])
    eq_('.', V['EFF']['Transcript_BioType'][0])
    eq_(1, V['EFF']['Gene_Coding'][0])
    eq_('NM_015658', V['EFF']['Transcript_ID'][0])
    eq_(-1, V['EFF']['Exon'][0])

    eq_('NON_SYNONYMOUS_CODING', V['EFF']['Effect'][1])
    eq_('MODERATE', V['EFF']['Effect_Impact'][1])
    eq_('MISSENSE', V['EFF']['Functional_Class'][1])
    eq_('gTt/gGt', V['EFF']['Codon_Change'][1])
    eq_('V155G', V['EFF']['Amino_Acid_Change'][1])
    eq_(-1, V['EFF']['Amino_Acid_Length'][1])
    eq_('PF3D7_0108900', V['EFF']['Gene_Name'][1])
    eq_('.', V['EFF']['Transcript_BioType'][1])
    eq_(-1, V['EFF']['Gene_Coding'][1])
    eq_('rna_PF3D7_0108900-1', V['EFF']['Transcript_ID'][1])
    eq_(1, V['EFF']['Exon'][1])

    eq_('.', V['EFF']['Effect'][2])
    eq_('.', V['EFF']['Effect_Impact'][2])
    eq_('.', V['EFF']['Functional_Class'][2])
    eq_('.', V['EFF']['Codon_Change'][2])
    eq_('.', V['EFF']['Amino_Acid_Change'][2])
    eq_(-1, V['EFF']['Amino_Acid_Length'][2])
    eq_('.', V['EFF']['Gene_Name'][2])
    eq_('.', V['EFF']['Transcript_BioType'][2])
    eq_(-1, V['EFF']['Gene_Coding'][2])
    eq_('.', V['EFF']['Transcript_ID'][2])
    eq_(-1, V['EFF']['Exon'][2])


def test_svlen():
    # V = variants('fixture/test13.vcf').view(np.recarray)
    # assert hasattr(V, 'svlen')
    # eq_(0, V.svlen[0])
    # eq_(1, V.svlen[1])
    # eq_(-1, V.svlen[2])
    # eq_(3, V.svlen[3])
    # eq_(3, V.svlen[4])
    V = variants('fixture/test13.vcf', arities={'svlen': 2}).view(np.recarray)
    # assert hasattr(V, 'svlen')
    # eq_((3, 0), tuple(V.svlen[3]))
    # eq_((3, -2), tuple(V.svlen[4]))


def test_duplicate_field_definitions():
    V = variants('fixture/test10.vcf')
    # should not raise, but print useful message to stderr
    C = calldata('fixture/test10.vcf')
    # should not raise, but print useful message to stderr


def test_missing_info_definition():
    # INFO field DP not declared in VCF header
    V = variants('fixture/test14.vcf', fields=['DP'])
    eq_('14', V[2]['DP'])  # default is string
    V = variants('fixture/test14.vcf', fields=['DP'], vcf_types={'DP':'Integer'})
    eq_(14, V[2]['DP'])
    # what about a field which isn't present at all?
    V = variants('fixture/test14.vcf', fields=['FOO'])
    eq_('.', V[2]['FOO'])  # default missing value for string field


def test_missing_format_definition():
    # FORMAT field DP not declared in VCF header
    C = calldata('fixture/test14.vcf', fields=['DP'], vcf_types={'DP':'Integer'})
    eq_(1, C[2]['NA00001']['DP'])


def test_explicit_pass_definition():
    # explicit PASS FILTER definition
    V = variants('fixture/test16.vcf')
    # should not raise