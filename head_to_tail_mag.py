# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import io
import json
import os
import random
from pathlib import Path

import zstandard as zstd

def ascii_ratio(x):
    c = 0
    for a in x:
        if a.isascii():
            c += 1
    return c / len(x) if x != "" else 0

DCTX = zstd.ZstdDecompressor(max_window_size=2**31)

def read_lines_from_zst_file(zstd_file_path:Path):
    with (
        zstd.open(zstd_file_path, mode='rb', dctx=DCTX) as zfh,
        io.TextIOWrapper(zfh) as iofh
    ):
        for line in iofh:
            yield line   

def main(kg_dir, working_dir):
    magconference = {}
    file = Path(os.path.join(kg_dir, 'ConferenceInstances.txt.zst'))
    for record in read_lines_from_zst_file(file):
        record = record.split("\t")
        if record[2] not in magconference:
            magconference[record[2]] = []
        magconference[record[2]].append(record)

    magconference_htt_l = []
    for x in magconference:
        if len(magconference[x]) == 1:
            magconference_htt_l.append(int(magconference[x][0][14]) if magconference[x][0][14].isdigit() else 0)

    magconference = [magconference[x][0] for x in magconference if len(magconference[x]) == 1]
    magconference.sort(key = lambda x:x[0])
    random.shuffle(magconference)

    magconference_htt_l.sort()
    magconference_htt_l_s = [0]
    for i in range(len(magconference_htt_l)):
        magconference_htt_l_s.append(magconference_htt_l_s[i] + magconference_htt_l[i])
    magconference_co1 = None
    magconference_co2 = None
    for i in range(len(magconference_htt_l)):
        if magconference_co1 is None and (magconference_htt_l_s[i+1] - magconference_htt_l_s[0]) / (magconference_htt_l_s[len(magconference_htt_l)] - magconference_htt_l_s[0]) >= 1./3.:
            magconference_co1 = i
        if magconference_co2 is None and (magconference_htt_l_s[i+1] - magconference_htt_l_s[0]) / (magconference_htt_l_s[len(magconference_htt_l)] - magconference_htt_l_s[0]) >= 2./3.:
            magconference_co2 = i

    magconferencegen = {"head": [], "torso": [], "tail": []}
    count = {}
    for x in ["head", "torso", "tail"]:
        count[x] = 0
    for i in range(len(magconference)):
        htt = int(magconference[i][14]) if magconference[i][14].isdigit() else 0
        if htt <= magconference_htt_l[magconference_co1]:
            htt = "tail"
        elif htt <= magconference_htt_l[magconference_co2]:
            htt = "torso"
        else:
            htt = "head"
        if magconference[i][2] != "" and magconference[i][4] != "" and count[htt] < 2000 and int(magconference[i][17][:4]) <= 2020 and ascii_ratio(magconference[i][2]) > 0.6:
            q = "Where was %s held?" % (magconference[i][2])
            a = magconference[i][4]
            magconferencegen[htt].append([magconference[i][0], "mag-conference-0", q, a])
            count[htt] += 1

    magjournal = {}
    file = Path(os.path.join(kg_dir, 'Journals.txt.zst'))
    for record in read_lines_from_zst_file(file):
        record = record.split("\t")
        if record[3] not in magjournal:
            magjournal[record[3]] = []
        magjournal[record[3]].append(record)

    magjournal_htt_l = []
    for x in magjournal:
        if len(magjournal[x]) == 1:
            magjournal_htt_l.append(int(magjournal[x][0][9]) if magjournal[x][0][9].isdigit() else 0)

    magjournal = [magjournal[x][0] for x in magjournal if len(magjournal[x]) == 1]
    magjournal.sort(key = lambda x:x[0])
    random.shuffle(magjournal)

    magjournal_htt_l.sort()
    magjournal_htt_l_s = [0]
    for i in range(len(magjournal_htt_l)):
        magjournal_htt_l_s.append(magjournal_htt_l_s[i] + magjournal_htt_l[i])
    magjournal_co1 = None
    magjournal_co2 = None
    for i in range(len(magjournal_htt_l)):
        if magjournal_co1 is None and (magjournal_htt_l_s[i+1] - magjournal_htt_l_s[0]) / (magjournal_htt_l_s[len(magjournal_htt_l)] - magjournal_htt_l_s[0]) >= 1./3.:
            magjournal_co1 = i
        if magjournal_co2 is None and (magjournal_htt_l_s[i+1] - magjournal_htt_l_s[0]) / (magjournal_htt_l_s[len(magjournal_htt_l)] - magjournal_htt_l_s[0]) >= 2./3.:
            magjournal_co2 = i

    magjournalgen = {"head": [], "torso": [], "tail": []}
    count = {}
    for x in ["head", "torso", "tail"]:
        count[x] = 0
    for i in range(len(magjournal)):
        htt = int(magjournal[i][9]) if magjournal[i][9].isdigit() else 0
        if htt <= magjournal_htt_l[magjournal_co1]:
            htt = "tail"
        elif htt <= magjournal_htt_l[magjournal_co2]:
            htt = "torso"
        else:
            htt = "head"
        if magjournal[i][3] != "" and magjournal[i][4] != "" and count[htt] < 2000 and int(magjournal[i][10][:4]) <= 2020 and ascii_ratio(magjournal[i][3]) > 0.6:
            q = "What's the ISSN of %s?" % (magjournal[i][3])
            a = magjournal[i][4]
            magjournalgen[htt].append([magjournal[i][0], "mag-journal-0", q, a])
            count[htt] += 1

    magpaper_htt_cnt = {}
    file = Path(os.path.join(kg_dir, 'Papers.txt.zst'))
    for record in read_lines_from_zst_file(file):
        record = record.split("\t")
        if record[7].isdigit() and int(record[7]) <= 2020:
            if record[19] not in magpaper_htt_cnt:
                magpaper_htt_cnt[record[19]] = 0
            magpaper_htt_cnt[record[19]] += 1

    magpaper_htt_cnt_l = [[int(x), magpaper_htt_cnt[x]] for x in magpaper_htt_cnt]
    magpaper_htt_cnt_l.sort(key = lambda x : x[0])
    magpaper_htt_cnt_l_s = [0]
    for i in range(len(magpaper_htt_cnt_l)):
        magpaper_htt_cnt_l_s.append(magpaper_htt_cnt_l_s[-1] + magpaper_htt_cnt_l[i][0] * magpaper_htt_cnt_l[i][1])
    magpaper_co1 = None
    magpaper_co2 = None
    for i in range(len(magpaper_htt_cnt_l)):
        if magpaper_co1 is None and (magpaper_htt_cnt_l_s[i+1] - magpaper_htt_cnt_l_s[0]) / (magpaper_htt_cnt_l_s[len(magpaper_htt_cnt_l)] - magpaper_htt_cnt_l_s[0]) >= 1./3.:
            magpaper_co1 = i
        if magpaper_co2 is None and (magpaper_htt_cnt_l_s[i+1] - magpaper_htt_cnt_l_s[0]) / (magpaper_htt_cnt_l_s[len(magpaper_htt_cnt_l)] - magpaper_htt_cnt_l_s[0]) >= 2./3.:
            magpaper_co2 = i

    s = [0, 0, 0]
    for i in range(len(magpaper_htt_cnt_l)):
        if magpaper_htt_cnt_l[i][0] <= magpaper_htt_cnt_l[magpaper_co1][0]:
            s[0] += magpaper_htt_cnt_l[i][1]
        elif magpaper_htt_cnt_l[i][0] <= magpaper_htt_cnt_l[magpaper_co2][0]:
            s[1] += magpaper_htt_cnt_l[i][1]
        else:
            s[2] += magpaper_htt_cnt_l[i][1]

    random.seed(42)
    magpaper_sample = {"head": [], "torso": [], "tail": []}
    file = Path(os.path.join(kg_dir, 'Papers.txt.zst'))
    for record in read_lines_from_zst_file(file):
        record = record.split("\t")
        if record[7].isdigit() and int(record[7]) <= 2020:
            r = random.random()
            if r < 10000 / s[0] and int(record[19]) <= magpaper_htt_cnt_l[magpaper_co1][0]:
                magpaper_sample["tail"].append(record)
            elif r < 10000 / s[1] and int(record[19]) <= magpaper_htt_cnt_l[magpaper_co2][0] and int(record[19]) > magpaper_htt_cnt_l[magpaper_co1][0]:
                magpaper_sample["torso"].append(record)
            elif r < 10000 / s[2] and int(record[19]) > magpaper_htt_cnt_l[magpaper_co2][0]:
                magpaper_sample["head"].append(record)

    maginterestpaperid = set()

    for x in ["head", "torso", "tail"]:
        for y in magpaper_sample[x]:
            maginterestpaperid.add(y[0])

    magpaper_sample_author = {}
    magextendedauthorid = set()

    file = Path(os.path.join(kg_dir, 'PaperAuthorAffiliations.txt.zst'))
    for record in read_lines_from_zst_file(file):
        record = record.split("\t")
        if record[0] in maginterestpaperid:
            if record[0] not in magpaper_sample_author:
                magpaper_sample_author[record[0]] = []
            magpaper_sample_author[record[0]].append(record)
            magextendedauthorid.add(record[1])

    magpaper_sample_author_detail = {}
    file = Path(os.path.join(kg_dir, 'Authors.txt.zst'))
    for record in read_lines_from_zst_file(file):
        record = record.split("\t")
        if record[0] in magextendedauthorid:
            assert(record[0] not in magpaper_sample_author_detail)
            magpaper_sample_author_detail[record[0]] = record

    maggen = {"head": [], "torso": [], "tail": []}

    for x in ["head", "torso", "tail"]:
        random.shuffle(magpaper_sample[x])
        count = [0, 0, 0, 0, 0, 0]
        for y in magpaper_sample[x]:
            if y[5] == "":
                continue
            if count[0] < 2000 and y[7] != "" and ascii_ratio(y[5]) > 0.6:
                q = "In which year was \"%s\" published?" % (y[5].rstrip("."))
                a = y[7]
                maggen[x].append([y[0], "mag-paper-0", q, a])
                count[0] += 1
            if count[1] < 2000 and y[21] != "" and ascii_ratio(y[5]) > 0.6 and ascii_ratio(y[21]) > 0.6:
                q = "In which venue was \"%s\" published?" % (y[5].rstrip("."))
                a = y[21]
                maggen[x].append([y[0], "mag-paper-1", q, a])
                count[1] += 1
            if count[2] < 2000 and y[10] != "" and "/" not in y[10] and ascii_ratio(y[5]) > 0.6:
                q = "Who is the publisher of \"%s\"?" % (y[5].rstrip("."))
                a = y[10]
                maggen[x].append([y[0], "mag-paper-2", q, a])
                count[2] += 1
            if count[3] < 2000 and y[2] != "" and ascii_ratio(y[5]) > 0.6:
                q = "What's the DOI of \"%s\"?" % (y[5].rstrip("."))
                a = y[2]
                maggen[x].append([y[0], "mag-paper-3", q, a])
                count[3] += 1
            if count[4] < 2000 and y[0] in magpaper_sample_author and len(magpaper_sample_author[y[0]]) != 0 and ascii_ratio(y[5]) > 0.6:
                q = "Who authored \"%s\"?" % (y[5].rstrip("."))
                a = []
                valid = True
                for r in magpaper_sample_author[y[0]]:
                    assert(magpaper_sample_author_detail[r[1]][3] != "")
                    a.append(magpaper_sample_author_detail[r[1]][3])
                if valid:
                    maggen[x].append([y[0], "mag-paper-4", q, a])
                    count[4] += 1

    output = {"head": [], "torso": [], "tail": []}
    for data in [maggen, magjournalgen, magconferencegen]:
        maxsample = {}
        for x in ["head", "torso", "tail"]:
            for i in range(len(data[x])):
                if data[x][i][1] not in maxsample:
                    maxsample[data[x][i][1]] = {}
                if x not in maxsample[data[x][i][1]]:
                    maxsample[data[x][i][1]][x] = 0
                maxsample[data[x][i][1]][x] += 1
        for x in maxsample:
            maxsample[x] = min(maxsample[x]["head"], maxsample[x]["torso"], maxsample[x]["tail"])

        for x in ["head", "torso", "tail"]:
            count = {}
            random.shuffle(data[x])
            for i in range(len(data[x])):
                if data[x][i][1] not in count:
                    count[data[x][i][1]] = 0
                if count[data[x][i][1]] < 100 and count[data[x][i][1]] < maxsample[data[x][i][1]]:
                    output[x] += [data[x][i]]
                    count[data[x][i][1]] += 1
            print(x, count)
    for x in ["head", "torso", "tail"]:
        random.shuffle(output[x])
        print(x, len(output[x]))
    with open(os.path.join(working_dir, "head_to_tail_mag.json"), "w", encoding='utf8') as f:
        json.dump(output, f, indent=1, ensure_ascii=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--kg-dir", type=str, default="./")
    parser.add_argument("--working-dir", type=str, default="./")
    args = parser.parse_args()
    
    main(args.kg_dir, args.working_dir)
