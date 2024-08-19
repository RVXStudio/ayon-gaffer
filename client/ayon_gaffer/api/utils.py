import os
import re

import pyseq


def get_pyseq_sequence(in_path):
    '''
    Takes a path and tries to get it's corresponding pyseq Sequence object
    '''
    print('Getting pyseq_path %s' % in_path)
    if os.path.isdir(in_path):
        print("get_pyseq_sequence does not want folders! [%s]" % in_path)
        return

    in_dir, in_name = os.path.split(in_path)
    seqs = pyseq.get_sequences(in_dir)

    for seq in seqs:
        test_name = in_name
        try:
            test_name = in_name % seq.start()
        except TypeError:
            pass
        if len(seq) == 1:
            print("Single frame!")
            return seq
        first_frame_padded = seq.format('%p') % seq.start()
        test_name = re.sub(r'#+', first_frame_padded, test_name)
        test_name = test_name.replace('*', first_frame_padded)
        test_name = re.sub(r'\{\d+\.\.\d+\}', first_frame_padded, test_name)

        i = pyseq.Item(test_name)
        if i.is_sibling(seq[0]) or seq[0].name == i.name:
            break
    else:
        print('could not find [{}]'.format(in_name))
        # we find nothing
        return None

    return seq
