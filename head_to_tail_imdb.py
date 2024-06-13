# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import gzip
import json
import os
import random

def main(kg_dir, working_dir):
    imdbbasics = {}
    with gzip.open(os.path.join(kg_dir, "title.basics.tsv.gz"), "rb") as f:
        imdbbasics_head = f.readline().decode().strip().split("\t")
        l = f.readline()
        while l:
            l = l.decode().strip().split("\t")
            assert len(l) == len(imdbbasics_head)
            if not (l[5] == "\\N" and l[6] == "\\N") and not (
                l[5] != "\\N" and int(l[5]) > 2020
            ):
                imdbbasics[l[0]] = l[1:]
            l = f.readline()

    imdbratings = {}
    with gzip.open(os.path.join(kg_dir, "title.ratings.tsv.gz"), "rb") as f:
        imdbratings_head = f.readline().decode().strip().split("\t")
        l = f.readline()
        while l:
            l = l.decode().strip().split("\t")
            assert len(l) == len(imdbratings_head)
            if l[0] in imdbbasics:
                imdbratings[l[0]] = l[1:]
            l = f.readline()

    imdbcrew = {}
    with gzip.open(os.path.join(kg_dir, "title.crew.tsv.gz"), "rb") as f:
        imdbcrew_head = f.readline().decode().strip().split("\t")
        l = f.readline()
        while l:
            l = l.decode().strip().split("\t")
            assert len(l) == len(imdbcrew_head)
            assert l[0] not in imdbcrew
            imdbcrew[l[0]] = l[1:]
            l = f.readline()

    imdbprincipals_nconst = {}
    with gzip.open(os.path.join(kg_dir, "title.principals.tsv.gz"), "rb") as f:
        l = f.readline()
        while l:
            l = l.decode().strip().split("\t")
            if l[2] not in ["", "\\N"] and l[5] not in ["", "\\N"]:
                if l[0] not in imdbprincipals_nconst:
                    imdbprincipals_nconst[l[0]] = {}
                if l[5] not in imdbprincipals_nconst[l[0]]:
                    imdbprincipals_nconst[l[0]][l[5]] = []
                imdbprincipals_nconst[l[0]][l[5]].append(l[2])
            l = f.readline()

    imdbname = {}
    imdbname_map_helper = {}
    with gzip.open(os.path.join(kg_dir, "name.basics.tsv.gz"), "rb") as f:
        imdbname_head = f.readline().decode().strip().split("\t")
        l = f.readline()
        while l:
            l = l.decode().strip().split("\t")
            assert len(l) == len(imdbname_head)
            knowfor = l[5].split(",")
            knowfor = [x for x in knowfor if x in imdbbasics or x == "\\N"]
            knowfor = ",".join(knowfor)
            if knowfor != "":
                imdbname[l[0]] = l[1:]
                imdbname[l[0]][4] = knowfor
            imdbname_map_helper[l[0]] = l[1].strip()
            l = f.readline()

    imdbbasics_htt = {}
    for x in imdbbasics:
        imdbbasics_htt[x] = int(imdbratings[x][1]) if x in imdbratings else 1
    imdbbasics_htt_l = []
    for x in imdbbasics_htt:
        imdbbasics_htt_l.append(imdbbasics_htt[x])
    imdbbasics_htt_l.sort()
    imdbbasics_htt_l_s = [0]
    for i in range(len(imdbbasics_htt_l)):
        imdbbasics_htt_l_s.append(imdbbasics_htt_l_s[i] + imdbbasics_htt_l[i])
    imdbbasics_co1 = None
    imdbbasics_co2 = None
    for i in range(len(imdbbasics_htt_l)):
        if (
            imdbbasics_co1 is None
            and (imdbbasics_htt_l_s[i + 1] - imdbbasics_htt_l_s[0])
            / (imdbbasics_htt_l_s[len(imdbbasics_htt_l)] - imdbbasics_htt_l_s[0])
            >= 1.0 / 3.0
        ):
            imdbbasics_co1 = i
        if (
            imdbbasics_co2 is None
            and (imdbbasics_htt_l_s[i + 1] - imdbbasics_htt_l_s[0])
            / (imdbbasics_htt_l_s[len(imdbbasics_htt_l)] - imdbbasics_htt_l_s[0])
            >= 2.0 / 3.0
        ):
            imdbbasics_co2 = i

    random.seed(42)
    imdbbasics_htt_head = []
    imdbbasics_htt_torso = []
    imdbbasics_htt_tail = []
    for x in imdbbasics_htt:
        if imdbbasics_htt[x] <= imdbbasics_htt_l[imdbbasics_co1]:
            imdbbasics_htt_tail.append(x)
        elif imdbbasics_htt[x] <= imdbbasics_htt_l[imdbbasics_co2]:
            imdbbasics_htt_torso.append(x)
        else:
            imdbbasics_htt_head.append(x)
    imdbbasics_htt_head.sort()
    imdbbasics_htt_torso.sort()
    imdbbasics_htt_tail.sort()
    random.shuffle(imdbbasics_htt_head)
    random.shuffle(imdbbasics_htt_torso)
    random.shuffle(imdbbasics_htt_tail)

    imdbbasics_freq = {}
    for x in imdbbasics:
        if imdbbasics[x][1] not in imdbbasics_freq:
            imdbbasics_freq[imdbbasics[x][1]] = 0
        imdbbasics_freq[imdbbasics[x][1]] += 1

    imdbname_freq = {}
    for x in imdbname:
        if imdbname[x][0] not in imdbname_freq:
            imdbname_freq[imdbname[x][0]] = 0
        imdbname_freq[imdbname[x][0]] += 1

    imdbname_htt = {}
    for x in imdbname:
        if imdbname_freq[imdbname[x][0]] == 1:
            imdbname_htt[x] = 0
            for y in imdbname[x][4].split(","):
                if y in imdbratings:
                    imdbname_htt[x] += int(imdbratings[y][1])
                elif y != "\\N":
                    imdbname_htt[x] += 1

    imdbname_htt_l = []
    for x in imdbname_htt:
        imdbname_htt_l.append(imdbname_htt[x])
    imdbname_htt_l.sort()
    imdbname_htt_l_s = [0]
    for i in range(len(imdbname_htt_l)):
        imdbname_htt_l_s.append(imdbname_htt_l_s[i] + imdbname_htt_l[i])
    imdbname_co1 = None
    imdbname_co2 = None
    for i in range(len(imdbname_htt_l)):
        if (
            imdbname_co1 is None
            and (imdbname_htt_l_s[i + 1] - imdbname_htt_l_s[0])
            / (imdbname_htt_l_s[len(imdbname_htt_l)] - imdbname_htt_l_s[0])
            >= 1.0 / 3.0
        ):
            imdbname_co1 = i
        if (
            imdbname_co2 is None
            and (imdbname_htt_l_s[i + 1] - imdbname_htt_l_s[0])
            / (imdbname_htt_l_s[len(imdbname_htt_l)] - imdbname_htt_l_s[0])
            >= 2.0 / 3.0
        ):
            imdbname_co2 = i

    imdbname_htt_head = []
    imdbname_htt_torso = []
    imdbname_htt_tail = []
    for x in imdbname_htt:
        if imdbname_htt[x] <= imdbname_htt_l[imdbname_co1]:
            if imdbname_htt[x] > 0:
                imdbname_htt_tail.append(x)
        elif imdbname_htt[x] <= imdbname_htt_l[imdbname_co2]:
            imdbname_htt_torso.append(x)
        else:
            imdbname_htt_head.append(x)
    imdbname_htt_head.sort()
    imdbname_htt_torso.sort()
    imdbname_htt_tail.sort()
    random.shuffle(imdbname_htt_head)
    random.shuffle(imdbname_htt_torso)
    random.shuffle(imdbname_htt_tail)

    imdbbasicssplit = [
        ["head", imdbbasics_htt_head],
        ["torso", imdbbasics_htt_torso],
        ["tail", imdbbasics_htt_tail],
    ]
    imdbbasicsgen = {"head": [], "torso": [], "tail": []}

    imdbname_map = lambda a: [imdbname_map_helper[x.strip()] for x in a.split(",")]
    for split in imdbbasicssplit:
        count = [0, 0, 0, 0, 0, 0, 0]
        for i in range(len(split[1])):
            basics = imdbbasics[split[1][i]]
            if (
                imdbbasics_freq[basics[1]] > 1
                and basics[4].isdigit()
                and int(basics[4]) <= 2020
            ):
                if "Series" in basics[0]:
                    count[0] += 1
                    if count[0] <= 2000:
                        q = "What's the series start year of %s?" % (basics[1])
                        a = int(basics[4])
                        imdbbasicsgen[split[0]].append([split[1][i], "imdb-title-0", q, a])
                else:
                    count[1] += 1
                    if count[1] <= 2000:
                        q = "In which year was %s released?" % (basics[1])
                        a = int(basics[4])
                        imdbbasicsgen[split[0]].append([split[1][i], "imdb-title-1", q, a])
            if basics[5].isdigit() and int(basics[5]) <= 2020:
                assert "Series" in basics[0]
                count[2] += 1
                if count[2] <= 2000:
                    assert basics[4].isdigit()
                    q = "What's the series end year of %s?" % (
                        basics[1]
                        if imdbbasics_freq[basics[1]] == 1
                        else basics[1] + " (" + basics[4] + ")"
                    )
                    a = int(basics[5])
                    imdbbasicsgen[split[0]].append([split[1][i], "imdb-title-2", q, a])
            if basics[6].isdigit():
                count[3] += 1
                if count[3] <= 2000:
                    q = "How long is the running time of %s (in minutes)?" % (
                        basics[1]
                        if imdbbasics_freq[basics[1]] == 1
                        else basics[1] + " (" + basics[4] + ")"
                    )
                    a = int(basics[6])
                    imdbbasicsgen[split[0]].append([split[1][i], "imdb-title-3", q, a])
            if split[1][i] in imdbcrew:
                if imdbcrew[split[1][i]][0] not in ["", "\\N"]:
                    count[4] += 1
                    if count[4] <= 2000:
                        q = "Who directed %s?" % (
                            basics[1]
                            if imdbbasics_freq[basics[1]] == 1
                            else basics[1] + " (" + basics[4] + ")"
                        )
                        a = imdbname_map(imdbcrew[split[1][i]][0])
                        imdbbasicsgen[split[0]].append([split[1][i], "imdb-title-4", q, a])
                if imdbcrew[split[1][i]][1] not in ["", "\\N"]:
                    count[5] += 1
                    if count[5] <= 2000:
                        q = "Who wrote %s?" % (
                            basics[1]
                            if imdbbasics_freq[basics[1]] == 1
                            else basics[1] + " (" + basics[4] + ")"
                        )
                        a = imdbname_map(imdbcrew[split[1][i]][1])
                        imdbbasicsgen[split[0]].append([split[1][i], "imdb-title-5", q, a])
            if split[1][i] in imdbprincipals_nconst:
                for c in imdbprincipals_nconst[split[1][i]]:
                    role = json.loads(c)
                    role = role[0]
                    count[6] += 1
                    if count[6] <= 2000 and role != "Self":
                        q = "Who played %s in %s?" % (
                            role,
                            basics[1]
                            if imdbbasics_freq[basics[1]] == 1
                            else basics[1] + " (" + basics[4] + ")",
                        )
                        a = imdbname_map(",".join(imdbprincipals_nconst[split[1][i]][c]))
                        imdbbasicsgen[split[0]].append([split[1][i], "imdb-title-6", q, a])

    imdbtitletypemap = {
        "tvPilot": "TV pilot",
        "tvMiniSeries": "TV mini series",
        "movie": "movie",
        "tvSeries": "TV series",
        "short": "short",
        "tvEpisode": "TV Episode",
        "tvSpecial": "TV Special",
        "videoGame": "video game",
        "video": "video",
        "tvShort": "TV short",
        "tvMovie": "TV movie",
    }
    imdbnameprofession_a = {
        "producer",
        "art_director",
        "production_designer",
        "assistant",
        "music_artist",
        "production_manager",
        "director",
        "casting_director",
        "assistant_director",
        "cinematographer",
        "actor",
        "manager",
        "podcaster",
        "publicist",
        "actress",
        "editor",
        "set_decorator",
        "writer",
        "talent_agent",
        "composer",
        "costume_designer",
        "choreographer",
        "executive",
    }
    imdbnameprofession_b = {
        "script_department",
        "camera_department",
        "electrical_department",
        "production_department",
        "art_department",
        "music_department",
        "animation_department",
        "location_management",
        "sound_department",
        "costume_department",
        "casting_department",
        "transportation_department",
        "make_up_department",
        "editorial_department",
    }
    imdbnameprofession_c = {
        "soundtrack",
        "legal",
        "stunts",
        "special_effects",
        "visual_effects",
    }
    imdbnamesplit = [
        ["head", imdbname_htt_head],
        ["torso", imdbname_htt_torso],
        ["tail", imdbname_htt_tail],
    ]
    imdbnamegen = {"head": [], "torso": [], "tail": []}
    for split in imdbnamesplit:
        count = [0, 0, 0, 0, 0, 0]
        for i in range(len(split[1])):
            name = imdbname[split[1][i]]
            if (
                name[1].isdigit()
                and int(name[1]) <= 2020
                and name[4] != "\\N"
                and name[4] != ""
            ):
                count[0] += 1
                if count[0] <= 2000:
                    q = "What is the birth year of %s (known for %s)?" % (
                        name[0],
                        imdbbasics[name[4].split(",")[0]][1]
                        + (
                            " (" + imdbbasics[name[4].split(",")[0]][4] + ")"
                            if imdbbasics_freq[imdbbasics[name[4].split(",")[0]][1]] > 1
                            and imdbbasics[name[4].split(",")[0]][4].isdigit()
                            else ""
                        ),
                    )
                    a = name[1]
                    imdbnamegen[split[0]].append([split[1][i], "imdb-name-0", q, a])
            if (
                name[2].isdigit()
                and int(name[2]) <= 2020
                and name[4] != "\\N"
                and name[4] != ""
            ):
                count[1] += 1
                if count[1] <= 2000:
                    q = "What is the death year of %s (known for %s)?" % (
                        name[0],
                        imdbbasics[name[4].split(",")[0]][1]
                        + (
                            " (" + imdbbasics[name[4].split(",")[0]][4] + ")"
                            if imdbbasics_freq[imdbbasics[name[4].split(",")[0]][1]] > 1
                            and imdbbasics[name[4].split(",")[0]][4].isdigit()
                            else ""
                        ),
                    )
                    a = name[2]
                    imdbnamegen[split[0]].append([split[1][i], "imdb-name-1", q, a])
            if name[3] != "\\N" and "," not in name[3] and name[3] != "":
                if name[3] in imdbnameprofession_a:
                    count[2] += 1
                    if count[2] <= 2000:
                        q = "What's the job of %s in %s?" % (
                            name[0],
                            imdbbasics[name[4].split(",")[0]][1]
                            + (
                                " (" + imdbbasics[name[4].split(",")[0]][4] + ")"
                                if imdbbasics_freq[imdbbasics[name[4].split(",")[0]][1]] > 1
                                and imdbbasics[name[4].split(",")[0]][4].isdigit()
                                else ""
                            ),
                        )
                        a = name[3].replace("_", " ")
                        imdbnamegen[split[0]].append([split[1][i], "imdb-name-2", q, a])
                elif name[3] in imdbnameprofession_b:
                    count[3] += 1
                    if count[3] <= 2000:
                        q = "%s (known for %s) is in what department?" % (
                            name[0],
                            imdbbasics[name[4].split(",")[0]][1]
                            + (
                                " (" + imdbbasics[name[4].split(",")[0]][4] + ")"
                                if imdbbasics_freq[imdbbasics[name[4].split(",")[0]][1]] > 1
                                and imdbbasics[name[4].split(",")[0]][4].isdigit()
                                else ""
                            ),
                        )
                        a = name[3].replace("_", " ")
                        imdbnamegen[split[0]].append([split[1][i], "imdb-name-3", q, a])
                elif name[3] in imdbnameprofession_c:
                    count[4] += 1
                    if count[4] <= 2000:
                        q = "What profession does %s (known for %s) have?" % (
                            name[0],
                            imdbbasics[name[4].split(",")[0]][1]
                            + (
                                " (" + imdbbasics[name[4].split(",")[0]][4] + ")"
                                if imdbbasics_freq[imdbbasics[name[4].split(",")[0]][1]] > 1
                                and imdbbasics[name[4].split(",")[0]][4].isdigit()
                                else ""
                            ),
                        )
                        a = name[3].replace("_", " ")
                        imdbnamegen[split[0]].append([split[1][i], "imdb-name-4", q, a])
            if name[4] != "\\N" and "," not in name[4] and name[4] != "":
                if imdbbasics[name[4].split(",")[0]][0] not in ["", "\\N"]:
                    count[5] += 1
                    if count[5] <= 2000:
                        q = "What %s is %s known for?" % (
                            imdbtitletypemap[imdbbasics[name[4].split(",")[0]][0]],
                            name[0],
                        )
                        a = imdbbasics[name[4].split(",")[0]][1]
                        imdbnamegen[split[0]].append([split[1][i], "imdb-name-5", q, a])

    output = {"head": [], "torso": [], "tail": []}
    questionset = set()
    for data in [imdbbasicsgen, imdbnamegen]:
        for x in data:
            for i in range(len(data[x]) - 1, -1, -1):
                if data[x][i][2].lower() in questionset:
                    del data[x][i]
                    continue
                questionset.add(data[x][i][2].lower())
        maxsample = {}
        for x in ["head", "torso", "tail"]:
            for i in range(len(data[x])):
                if data[x][i][1] not in maxsample:
                    maxsample[data[x][i][1]] = {}
                if x not in maxsample[data[x][i][1]]:
                    maxsample[data[x][i][1]][x] = 0
                maxsample[data[x][i][1]][x] += 1
        for x in maxsample:
            maxsample[x] = min(
                maxsample[x]["head"], maxsample[x]["torso"], maxsample[x]["tail"]
            )

        for x in ["head", "torso", "tail"]:
            count = {}
            random.shuffle(data[x])
            for i in range(len(data[x])):
                if data[x][i][1] not in count:
                    count[data[x][i][1]] = 0
                if (
                    count[data[x][i][1]] < 85
                    and count[data[x][i][1]] < maxsample[data[x][i][1]]
                ):
                    output[x] += [data[x][i]]
                    count[data[x][i][1]] += 1
            print(x, count)
    for x in ["head", "torso", "tail"]:
        random.shuffle(output[x])
        print(x, len(output[x]))

    with open(os.path.join(working_dir, "head_to_tail_imdb.json"), "w", encoding="utf8") as f:
        json.dump(output, f, indent=1, ensure_ascii=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--kg-dir", type=str, default="./")
    parser.add_argument("--working-dir", type=str, default="./")
    args = parser.parse_args()
    
    main(args.kg_dir, args.working_dir)
