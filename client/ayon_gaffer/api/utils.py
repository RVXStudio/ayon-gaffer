import os
import re

import pyseq

from ayon_core.lib import Logger
log = Logger.get_logger("ayon_gaffer.api.utils")


def get_pyseq_sequence(in_path, frame_start=None, frame_end=None):
    '''
    Takes a path and tries to get it's corresponding pyseq Sequence object.

    Args:
        in_path (str): The path to the file or sequence.

    Returns:
        (pyseq.Sequence): The sequence containing the input `in_path`.

    '''
    log.info('Getting pyseq_path %s' % in_path)
    if os.path.isdir(in_path):
        log.error("get_pyseq_sequence does not want folders! [%s]" % in_path)
        return

    in_dir, in_name = os.path.split(in_path)
    if not os.path.exists(in_dir):
        log.error(f"Directory [{in_dir}] does not exist")
        return

    # first check if there is a frame there

    expr = re.compile(r"(?P<head>.*[\.])(?P<frame>\d+)(?P<tail>[\.][a-zA-Z0-9\.]+$)")
    dir_files = os.listdir(in_dir)
    res = re.search(expr, in_name)
    if res is None:
        # what are we even doing here?
        interesting_files = [os.path.join(in_dir, f) for f in dir_files]
        head = tail = frame = None
    else:
        head = res.group("head")
        tail = res.group("tail")
        frame_padding = len(res.group("frame"))
        frame = int(res.group("frame"))
        interesting_files = []

        for dir_file in dir_files:
            if dir_file.startswith(head):
                interesting_files.append(os.path.join(in_dir, dir_file))
    seqs = pyseq.get_sequences(interesting_files)
    for seq in seqs:
        test_name = in_name
        try:
            test_name = in_name % seq.start()
        except TypeError:
            pass
        if seq.length() == 1:
            if test_name == seq[0].name:
                # this is the same file, right?
                break
        else:
            first_frame_padded = seq.format('%p') % seq.start()
            # replace hash padding with the first frame of the sequence
            test_name = re.sub(r'#+', first_frame_padded, test_name)
            # replace * with the first frame number
            test_name = test_name.replace('*', first_frame_padded)
            # replace {1..2} formatting with the first frame number
            test_name = re.sub(r'\{\d+\.\.\d+\}', first_frame_padded, test_name)

            i = pyseq.Item(test_name)
            if i.is_sibling(seq[0]) or seq[0].name == i.name:
                break
    else:
        log.debug('could not find [{}]'.format(in_name))
        # we find nothing, try to construct pyseq object
        return

        return None
    # make single frame seqs become multi-frame
    if len(seq) == 1 and frame is not None:
        next_frame = frame + 1
        next_path = f"{in_dir}/{head}{str(next_frame).zfill(frame_padding)}{tail}"
        seq = pyseq.Sequence([in_path, next_path])
        seq.remove(seq[1])
    return seq