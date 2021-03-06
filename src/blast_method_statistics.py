from repeat_finder import *
from sam_utils import *
from Bio import SeqIO
from blast_wrapper import get_blast_matched_ids


def get_exact_number_of_repeats_from_sequence(pattern, pattern_start):
    file_name = 'chr15.fa'
    fasta_sequences = SeqIO.parse(open(file_name), 'fasta')
    sequence = ''
    for fasta in fasta_sequences:
        name, sequence = fasta.id, str(fasta.seq)
    corresponding_region_in_seq = sequence[pattern_start:pattern_start + len(pattern) * 35].upper()
    repeats, seqs = get_number_of_occurrence_of_pattern_in_text(corresponding_region_in_seq, pattern, 0.66, True)
    return repeats, seqs


def find_sensitivity_of_blast_method(pattern_num, pattern, related_reads, word_size, evalue, min_length_for_pattern):
    blast_pattern = pattern
    if min_length_for_pattern and len(pattern) < min_length_for_pattern:
        blast_pattern = pattern * int(round(50.0 / len(pattern) + 0.5))

    blast_selected_reads = get_blast_matched_ids(blast_pattern, 'original_reads/original_reads', max_seq='6000',
                                                 word_size=word_size, evalue=evalue, search_id=str(pattern_num))

    TP = [read for read in blast_selected_reads if read in related_reads]
    FP = [read for read in blast_selected_reads if read not in TP]
    FN = [read for read in related_reads if read not in blast_selected_reads]
    print('TP:', len(TP), 'FP:', len(FP), 'blast selected:', len(blast_selected_reads))
    print('FN:', len(FN))
    sensitivity = float(len(TP)) / len(related_reads) if len(related_reads) > 0 else 0
    # false_discover_rate = float(len(FP)) / (len(FP) + len(TP)) if (len(FP) + len(TP)) > 0 else 0
    min_len = min_length_for_pattern if min_length_for_pattern else 0
    param = word_size if word_size else evalue
    used_param = 'word_size' if word_size else 'evalue'
    with open('FP_and_sensitivity_%s_min_len%s.txt' % (used_param, min_len), 'a') as outfile:
        outfile.write('%s\t%s\t%s\t%s\t%s\t%s\n' % (len(FP), sensitivity, param, pattern_num, len(pattern), len(TP)))


def find_sensitivity_curve_of_blast_method(pattern_num, pattern, pattern_start, min_length_for_pattern=None):
    repeats, repeat_seqs = get_exact_number_of_repeats_from_sequence(pattern, pattern_start)
    related_reads, read_counts = get_related_reads_and_read_count_in_samfile(pattern, pattern_start, repeats, 'original_reads/paired_dat.sam')
    N = read_counts - len(related_reads)

    for evalue in [1e-20, 1e-17, 1e-15, 1e-12, 1e-9, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]:
        find_sensitivity_of_blast_method(pattern_num, pattern, related_reads, None, evalue, min_length_for_pattern)
    for word_size in [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]:
        word_size = str(word_size)
        find_sensitivity_of_blast_method(pattern_num, pattern, related_reads, word_size, 10.0, min_length_for_pattern)


def write_cn_over_true_cn_to_files(patterns, start_points, repeat_count):
    # read_files = [['paired_dat1.fasta', 'paired_dat2.fasta'],
    # ['paired_dat1.fasta', 'paired_dat2.fasta', 'edited_chr15_paired_dat1.fasta', 'edited_chr15_paired_dat2.fasta']]
    # out_files = ['original_computed_cn.txt', 'diploid_computed_cn.txt']
    # directory = ['original_reads/', 'diploid/']

    out_files = ['10X_ratio.txt', '20X_ratio.txt', '30X_ratio.txt']
    read_files = [['10X_paired_dat1.fasta', '10X_paired_dat2.fasta'],
                  ['paired_dat1.fasta', 'paired_dat2.fasta'],
                  ['30X_paired_dat1.fasta', '30X_paired_dat2.fasta']]
    directory = ['10X_reads/', 'original_reads/', '30X_reads/']

    for k in range(len(out_files)):
        if k != 1:
            continue
        db_name = 'blast_db'
        if len(directory[k]):
            db_name = directory[k][:len(directory[k]) - 1]
        blast_db_name = directory[k] + db_name
        for t in range(len(read_files[k])):
            read_files[k][t] = directory[k] + read_files[k][t]
        # make_blast_database(read_files[k], blast_db_name)

        for i in range(len(patterns)):
            print(i)
            if repeat_count[i] == 0:
                continue
            calculated_cn = get_copy_number_of_pattern(patterns[i], read_files[k], directory[k], min_len=50)
            with open(out_files[k], 'a') as outfile:
                outfile.write('%s %s\n' % (i, calculated_cn / repeat_count[i]))


with open('patterns.txt') as input:
    patterns = input.readlines()
    patterns = [pattern.strip() for pattern in patterns]
with open('start_points.txt') as input:
    lines = input.readlines()
    start_points = [int(num.strip())-1 for num in lines]
with open('pattern_repeat_counts.txt') as input:
    lines = input.readlines()
    repeat_count = [int(num.strip()) for num in lines]

write_cn_over_true_cn_to_files(patterns, start_points, repeat_count)

# for i in range(len(patterns)):
#     print(i)
#     find_sensitivity_curve(i+1, patterns[i], start_points[i], 50.0)
