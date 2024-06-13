# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import json
import os
import random

from dblp_parser import DBLP

def main(kg_dir, working_dir):
    input_path = os.path.join(working_dir, "dblp.jsonl")
    dblp = DBLP()
    dblp.parse_all(os.path.join(kg_dir, "dblp.xml"), input_path)

    dblp_author = {}
    dblp_author2 = {}
    dblp_author3 = {}
    with open(input_path, "r", encoding='utf8') as f:
        l = f.readline()
        while l:
            l = json.loads(l)
            for i in range(len(l["author"])):
                if l["author"][i] not in dblp_author:
                    dblp_author[l["author"][i]] = 0
                dblp_author[l["author"][i]] += 1
                author = l["author"][i].split()
                if author[-1].isdigit():
                    author = author[:-1]
                author = " ".join(author)
                if author not in dblp_author2:
                    dblp_author2[author] = 0
                dblp_author2[author] += 1
                if author not in dblp_author3:
                    dblp_author3[author] = set()
                dblp_author3[author].add(l["author"][i])
            for i in range(len(l["editor"])):
                if l["editor"][i] not in dblp_author:
                    dblp_author[l["editor"][i]] = 0
                dblp_author[l["editor"][i]] += 1
                author = l["editor"][i].split()
                if author[-1].isdigit():
                    author = author[:-1]
                author = " ".join(author)
                if author not in dblp_author2:
                    dblp_author2[author] = 0
                dblp_author2[author] += 1
                if author not in dblp_author3:
                    dblp_author3[author] = set()
                dblp_author3[author].add(l["editor"][i])
            l = f.readline()

    dblpname_htt_l = []
    for x in dblp_author2:
        if len(dblp_author3[x]) > 1:
            continue
        dblpname_htt_l.append(dblp_author2[x])
    dblpname_htt_l.sort()
    dblpname_htt_l_s = [0]
    for i in range(len(dblpname_htt_l)):
        dblpname_htt_l_s.append(dblpname_htt_l_s[i] + dblpname_htt_l[i])
    dblpname_co1 = None
    dblpname_co2 = None
    for i in range(len(dblpname_htt_l)):
        if dblpname_co1 is None and (dblpname_htt_l_s[i+1] - dblpname_htt_l_s[0]) / (dblpname_htt_l_s[len(dblpname_htt_l)] - dblpname_htt_l_s[0]) >= 1./3.:
            dblpname_co1 = i
        if dblpname_co2 is None and (dblpname_htt_l_s[i+1] - dblpname_htt_l_s[0]) / (dblpname_htt_l_s[len(dblpname_htt_l)] - dblpname_htt_l_s[0]) >= 2./3.:
            dblpname_co2 = i

    random.seed(42)
    dblpname_htt_head = {}
    dblpname_htt_torso = {}
    dblpname_htt_tail = {}
    dblpname_mastersthesis = set()
    with open(input_path, "r", encoding='utf8') as f:
        l = f.readline()
        while l:
            l = json.loads(l)
            if l["type"] == 'mastersthesis':
                if len(l["author"]) == 1:
                    author = l["author"][0].split()
                    if author[-1].isdigit():
                        author = author[:-1]
                    author = " ".join(author)
                    if len(dblp_author3[author]) == 1:
                        dblpname_mastersthesis.add(author)
            l = f.readline()

    for x in dblp_author2:
        if len(dblp_author3[x]) > 1:
            continue
        r = random.random()
        if x in dblpname_mastersthesis or (dblp_author2[x] > dblpname_htt_l[dblpname_co2] and r < 0.12) or (dblp_author2[x] > dblpname_htt_l[dblpname_co1] and r < 0.025) or (dblp_author2[x] <= dblpname_htt_l[dblpname_co1] and r < 0.025):
            if dblp_author2[x] <= dblpname_htt_l[dblpname_co1]:
                dblpname_htt_tail[x] = {"phd": [], "ms": [], "author": [], "editor": []}
            elif dblp_author2[x] <= dblpname_htt_l[dblpname_co2]:
                dblpname_htt_torso[x] = {"phd": [], "ms": [], "author": [], "editor": []}
            else:
                dblpname_htt_head[x] = {"phd": [], "ms": [], "author": [], "editor": []}

    with open(input_path, "r", encoding='utf8') as f:
        l = f.readline()
        while l:
            l = json.loads(l)
            if l["type"] == 'phdthesis':
                for i in range(len(l["author"])):
                    author = l["author"][i]
                    if author in dblpname_htt_tail: 
                        if len(l["author"]) > 1 or dblpname_htt_tail[author]["phd"] != []:
                            dblpname_htt_tail[author]["phd"] = None
                        else:
                            dblpname_htt_tail[author]["phd"].append(l)
                    elif author in dblpname_htt_torso: 
                        if len(l["author"]) > 1 or dblpname_htt_torso[author]["phd"] != []:
                            dblpname_htt_torso[author]["phd"] = None
                        else:
                            dblpname_htt_torso[author]["phd"].append(l)
                    elif author in dblpname_htt_head: 
                        if len(l["author"]) > 1 or dblpname_htt_head[author]["phd"] != []:
                            dblpname_htt_head[author]["phd"] = None
                        else:
                            dblpname_htt_head[author]["phd"].append(l)
            elif l["type"] == 'mastersthesis':
                for i in range(len(l["author"])):
                    author = l["author"][i]
                    if author in dblpname_htt_tail: 
                        if len(l["author"]) > 1 or dblpname_htt_tail[author]["ms"] != []:
                            dblpname_htt_tail[author]["ms"] = None
                        else:
                            dblpname_htt_tail[author]["ms"].append(l)
                    elif author in dblpname_htt_torso: 
                        if len(l["author"]) > 1 or dblpname_htt_torso[author]["ms"] != []:
                            dblpname_htt_torso[author]["ms"] = None
                        else:
                            dblpname_htt_torso[author]["ms"].append(l)
                    elif author in dblpname_htt_head: 
                        if len(l["author"]) > 1 or dblpname_htt_head[author]["ms"] != []:
                            dblpname_htt_head[author]["ms"] = None
                        else:
                            dblpname_htt_head[author]["ms"].append(l)
            for ae in ["author", "editor"]:
                for i in range(len(l[ae])):
                    author = l[ae][i]
                    if author in dblpname_htt_tail: 
                        dblpname_htt_tail[author][ae].append(l)
                    elif author in dblpname_htt_torso: 
                        dblpname_htt_torso[author][ae].append(l)
                    elif author in dblpname_htt_head: 
                        dblpname_htt_head[author][ae].append(l)
            l = f.readline()

    dblpname_htt_head = [[x, dblpname_htt_head[x]] for x in dblpname_htt_head]
    dblpname_htt_torso = [[x, dblpname_htt_torso[x]] for x in dblpname_htt_torso]
    dblpname_htt_tail = [[x, dblpname_htt_tail[x]] for x in dblpname_htt_tail]
    random.shuffle(dblpname_htt_head)
    random.shuffle(dblpname_htt_torso)
    random.shuffle(dblpname_htt_tail)

    dblpnamesplit = [["head", dblpname_htt_head], ["torso", dblpname_htt_torso], ["tail", dblpname_htt_tail]]
    dblpnamegen = {"head": [], "torso": [], "tail": []}

    for split in dblpnamesplit:
        count = [0, 0, 0, 0, 0, 0]
        for i in range(len(split[1])):
            name, rec = split[1][i]
            if count[0] < 2000 and rec["phd"] is not None and rec["phd"] != [] and rec["phd"][0]["title"] != "" and rec["phd"][0]["school"] != "" and rec["phd"][0]["year"].isdigit():
                if int(rec["phd"][0]["year"]) <= 2020:
                    q = "What's the Ph.D. thesis of %s from %s in %s?" % (name, rec["phd"][0]["school"], rec["phd"][0]["year"])
                    a = rec["phd"][0]["title"]
                    dblpnamegen[split[0]].append([rec["phd"][0], "dblp-name-0", q, a])
                    count[0] += 1
            if count[1] < 2000 and rec["ms"] is not None and rec["ms"] != [] and rec["ms"][0]["title"] != "" and rec["ms"][0]["school"] != "" and rec["ms"][0]["year"].isdigit():
                if int(rec["ms"][0]["year"]) <= 2020:
                    q = "What's the master's thesis of %s from %s in %s?" % (name, rec["ms"][0]["school"], rec["ms"][0]["year"])
                    a = rec["ms"][0]["title"]
                    dblpnamegen[split[0]].append([rec["ms"][0], "dblp-name-1", q, a])
                    count[1] += 1
            if count[2] < 2000 and rec["phd"] is not None and rec["phd"] != [] and rec["phd"][0]["title"] != "" and rec["phd"][0]["school"] != "" and rec["phd"][0]["year"].isdigit():
                if int(rec["phd"][0]["year"]) <= 2020:
                    q = "In which year did %s receive the Ph.D. from %s?" % (name, rec["phd"][0]["school"])
                    a = rec["phd"][0]["year"]
                    dblpnamegen[split[0]].append([rec["phd"][0], "dblp-name-2", q, a])
                    count[2] += 1
            if count[3] < 2000 and rec["ms"] is not None and rec["ms"] != [] and rec["ms"][0]["title"] != "" and rec["ms"][0]["school"] != "" and rec["ms"][0]["year"].isdigit():
                if int(rec["ms"][0]["year"]) <= 2020:
                    q = "In which year did %s receive the master's degree from %s?" % (name, rec["ms"][0]["school"])
                    a = rec["ms"][0]["year"]
                    dblpnamegen[split[0]].append([rec["ms"][0], "dblp-name-3", q, a])
                    count[3] += 1
            if count[4] < 2000 and rec["phd"] is not None and rec["phd"] != [] and rec["phd"][0]["title"] != "" and rec["phd"][0]["school"] != "" and rec["phd"][0]["year"].isdigit():
                if int(rec["phd"][0]["year"]) <= 2020:
                    q = "Where did %s receive the Ph.D. (thesis: %s)?" % (name, rec["phd"][0]["title"])
                    a = rec["phd"][0]["school"]
                    dblpnamegen[split[0]].append([rec["phd"][0], "dblp-name-4", q, a])
                    count[4] += 1
            if count[5] < 2000 and rec["ms"] is not None and rec["ms"] != [] and rec["ms"][0]["title"] != "" and rec["ms"][0]["school"] != "" and rec["ms"][0]["year"].isdigit():
                if int(rec["ms"][0]["year"]) <= 2020:
                    q = "Where did %s receive the master's degree (thesis: %s)?" % (name, rec["ms"][0]["title"])
                    a = rec["ms"][0]["school"]
                    dblpnamegen[split[0]].append([rec["ms"][0], "dblp-name-5", q, a])
                    count[5] += 1

    output = {"head": [], "torso": [], "tail": []}
    questionset = set()
    for x in dblpnamegen:
        for i in range(len(dblpnamegen[x]) - 1, -1, -1):
            if "&#" in dblpnamegen[x][i][3] or dblpnamegen[x][i][2].lower() in questionset:
                del dblpnamegen[x][i]
                continue
            questionset.add(dblpnamegen[x][i][2].lower())
    maxsample = {}
    for x in ["head", "torso", "tail"]:
        for i in range(len(dblpnamegen[x])):
            if dblpnamegen[x][i][1] not in maxsample:
                maxsample[dblpnamegen[x][i][1]] = {}
            if x not in maxsample[dblpnamegen[x][i][1]]:
                maxsample[dblpnamegen[x][i][1]][x] = 0
            maxsample[dblpnamegen[x][i][1]][x] += 1
    for x in maxsample:
        maxsample[x] = min(maxsample[x]["head"], maxsample[x]["torso"], maxsample[x]["tail"])

    for x in ["head", "torso", "tail"]:
        count = {}
        random.shuffle(dblpnamegen[x])
        for i in range(len(dblpnamegen[x])):
            if dblpnamegen[x][i][1] not in count:
                count[dblpnamegen[x][i][1]] = 0
            if count[dblpnamegen[x][i][1]] < 100 and count[dblpnamegen[x][i][1]] < maxsample[dblpnamegen[x][i][1]]:
                output[x].append(dblpnamegen[x][i])
                count[dblpnamegen[x][i][1]] += 1
        print(x, count)

    for x in ["head", "torso", "tail"]:
        random.shuffle(output[x])
        print(x, len(output[x]))
        
    with open(os.path.join(working_dir, "head_to_tail_dblp.json"), "w", encoding='utf8') as f:
        json.dump(output, f, indent=1, ensure_ascii=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--kg-dir", type=str, default="./")
    parser.add_argument("--working-dir", type=str, default="./")
    args = parser.parse_args()
    
    main(args.kg_dir, args.working_dir)
