# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import bz2
import json
import os
import random
from urllib.parse import unquote

def main(kg_dir, working_dir):
    entity = {}
    relation = {}
    with bz2.open(
        os.path.join(kg_dir, "mappingbased-objects_lang=en.ttl.bz2"), mode="rt"
    ) as f:
        for line in f:
            line = line.strip().strip(".")
            cnt = 0
            block = 0
            start = 0
            for i in range(len(line)):
                if line[i] == "<":
                    cnt += 1
                elif line[i] == ">":
                    cnt -= 1
                    if cnt == 0:
                        x = line[start : i + 1].strip()
                        start = i + 1
                        if block == 0 or block == 2:
                            if x not in entity:
                                entity[x] = 0
                            entity[x] += 1
                        else:
                            if x not in relation:
                                relation[x] = 0
                            relation[x] += 1
                        block += 1

    relation_sorted = [[x, relation[x]] for x in relation]
    relation_sorted.sort(key=lambda x: -x[1])
    entity_sorted = [[x, entity[x]] for x in entity]
    entity_sorted.sort(key=lambda x: -x[1])

    dbpedia_entity_htt_l = []
    for x in entity_sorted:
        dbpedia_entity_htt_l += [x[1]]
    dbpedia_entity_htt_l.sort()
    dbpedia_entity_htt_l_s = [0]
    for i in range(len(dbpedia_entity_htt_l)):
        dbpedia_entity_htt_l_s += [dbpedia_entity_htt_l_s[i] + dbpedia_entity_htt_l[i]]
    dbpedia_entity_co1 = None
    dbpedia_entity_co2 = None
    for i in range(len(dbpedia_entity_htt_l)):
        if (
            dbpedia_entity_co1 is None
            and (dbpedia_entity_htt_l_s[i + 1] - dbpedia_entity_htt_l_s[0])
            / (
                dbpedia_entity_htt_l_s[len(dbpedia_entity_htt_l)]
                - dbpedia_entity_htt_l_s[0]
            )
            >= 1.0 / 3.0
        ):
            dbpedia_entity_co1 = i
        if (
            dbpedia_entity_co2 is None
            and (dbpedia_entity_htt_l_s[i + 1] - dbpedia_entity_htt_l_s[0])
            / (
                dbpedia_entity_htt_l_s[len(dbpedia_entity_htt_l)]
                - dbpedia_entity_htt_l_s[0]
            )
            >= 2.0 / 3.0
        ):
            dbpedia_entity_co2 = i

    relation_htt_stat = {"head": {}, "torso": {}, "tail": {}}
    with bz2.open(
        os.path.join(kg_dir, "mappingbased-objects_lang=en.ttl.bz2"), mode="rt"
    ) as f:
        for line in f:
            line = line.strip().strip(".")
            cnt = 0
            start = 0
            triple = []
            for i in range(len(line)):
                if line[i] == "<":
                    cnt += 1
                elif line[i] == ">":
                    cnt -= 1
                    if cnt == 0:
                        x = line[start : i + 1].strip()
                        start = i + 1
                        triple += [x]
            if entity[triple[0]] <= dbpedia_entity_htt_l[dbpedia_entity_co1]:
                htt = "tail"
            elif entity[triple[0]] <= dbpedia_entity_htt_l[dbpedia_entity_co2]:
                htt = "torso"
            else:
                htt = "head"
            if triple[1] not in relation_htt_stat[htt]:
                relation_htt_stat[htt][triple[1]] = 0
            relation_htt_stat[htt][triple[1]] += 1

    with open(
        "dbpedia_question_templates.json",
        "r",
        encoding="utf8",
    ) as f:
        dbpedia_template = json.load(f)

    random.seed(42)
    dbpediagen = {"head": [], "torso": [], "tail": []}
    current = [None, None]
    records = []
    currenthtt = None
    with bz2.open(
        os.path.join(kg_dir, "mappingbased-objects_lang=en.ttl.bz2"), mode="rt"
    ) as f:
        for line in f:
            line = line.strip().strip(".")
            cnt = 0
            start = 0
            triple = []
            for i in range(len(line)):
                if line[i] == "<":
                    cnt += 1
                elif line[i] == ">":
                    cnt -= 1
                    if cnt == 0:
                        x = line[start : i + 1].strip()
                        start = i + 1
                        triple += [x]
            if entity[triple[0]] <= dbpedia_entity_htt_l[dbpedia_entity_co1]:
                htt = "tail"
            elif entity[triple[0]] <= dbpedia_entity_htt_l[dbpedia_entity_co2]:
                htt = "torso"
            else:
                htt = "head"
            if triple[:2] != current:
                if len(records) == 1:
                    if current[1] in dbpedia_template:
                        r = random.random()
                        if r < 10000 / relation_htt_stat[currenthtt][current[1]]:
                            A = unquote(records[0][0].split("/")[-1][:-1])
                            B = unquote(
                                records[0][2].split("dbpedia.org/resource/")[-1][:-1]
                            )
                            if "__" not in A and "__" not in B:
                                A = A.replace("_", " ")
                                B = B.replace("_", " ")

                                if B.lower() not in A.lower():
                                    q = dbpedia_template[current[1]].replace("_", A)
                                    a = B
                                    dbpediagen[currenthtt] += [
                                        [records[0], current[1], q, a]
                                    ]
                current = triple[:2]
                records = [triple]
                currenthtt = htt
            else:
                records += [triple]

    def cleaning_rules(rel, ans):
        if rel == "<http://dbpedia.org/ontology/category>":
            return True
        if rel == "<http://dbpedia.org/ontology/isPartOf>":
            return True
        if type(ans) == str:
            if rel == "<http://dbpedia.org/ontology/computingPlatform>" and ans == "Cross-platform":
                return True
            if rel == "<http://dbpedia.org/ontology/typeOfElectrification>" and ans in ["Volts", "Volt"]:
                return True
            if rel == "<http://dbpedia.org/ontology/militaryRank>" and ans.startswith("Military ranks "):
                return True
            if rel == "<http://dbpedia.org/ontology/operatingSystem>" and ans.endswith("system software"):
                return True
            if rel == "<http://dbpedia.org/ontology/deathCause>" and ans == "Death":
                return True
            if rel == "<http://dbpedia.org/ontology/deathCause>" and ans.startswith("Death of "):
                return True
            if rel == "<http://dbpedia.org/ontology/deathCause>" and ans.startswith("Killing of "):
                return True
            if rel == "<http://dbpedia.org/ontology/notableCommander>" and ans in ["Major general", "General"]:
                return True
            if rel == "<http://dbpedia.org/ontology/ethnicGroup>" and ans.startswith("Ethnic groups "):
                return True
            if rel == "<http://dbpedia.org/ontology/island>" and ans == "Islands":
                return True
            if rel == "<http://dbpedia.org/ontology/presenter>" and ans.endswith("Awards"):
                return True
            if rel == "<http://dbpedia.org/ontology/symptom>" and ans == "Symptoms":
                return True
            if rel == "<http://dbpedia.org/ontology/honours>" and ans.startswith("Honours of "):
                return True
            if rel == "<http://dbpedia.org/ontology/canton>" and ans.startswith("Cantons of "):
                return True
            if rel == "<http://dbpedia.org/ontology/battery>" and ans in ["KWh", "Kilowatt-hour"]:
                return True
            if rel == "<http://dbpedia.org/ontology/college>" and ans.endswith("basketball"):
                return True
            if ans.startswith("List of "):
                return True
        return False

    output = {"head": [], "torso": [], "tail": []}
    maxsample = {}
    for x in ["head", "torso", "tail"]:
        for i in range(len(dbpediagen[x])):
            if type(dbpediagen[x][i][3]) == str and dbpediagen[x][i][3].startswith("<http"):
                if dbpediagen[x][i][1] not in [
                    "<http://xmlns.com/foaf/0.1/page>",
                    "<http://xmlns.com/foaf/0.1/homepage>",
                    "<http://dbpedia.org/ontology/webcast>",
                ]:
                    continue
                dbpediagen[x][i][3] = dbpediagen[x][i][3][1:]
            if cleaning_rules(dbpediagen[x][i][1], dbpediagen[x][i][3]):
                continue
            if "<http://dbpedia.org/resource/List_of_" in dbpediagen[x][i][0][0]:
                continue
            if dbpediagen[x][i][1] not in maxsample:
                maxsample[dbpediagen[x][i][1]] = {}
            if x not in maxsample[dbpediagen[x][i][1]]:
                maxsample[dbpediagen[x][i][1]][x] = 0
            maxsample[dbpediagen[x][i][1]][x] += 1
    for x in maxsample:
        maxsample[x] = min(
            maxsample[x]["head"] if "head" in maxsample[x] else 0,
            maxsample[x]["torso"] if "torso" in maxsample[x] else 0,
            maxsample[x]["tail"] if "tail" in maxsample[x] else 0,
        )

    for x in ["tail", "torso", "head"]:
        stat = {}
        random.shuffle(dbpediagen[x])
        for i in range(len(dbpediagen[x])):
            if type(dbpediagen[x][i][3]) == str and dbpediagen[x][i][3].startswith("<http"):
                if dbpediagen[x][i][1] not in [
                    "<http://xmlns.com/foaf/0.1/page>",
                    "<http://xmlns.com/foaf/0.1/homepage>",
                    "<http://dbpedia.org/ontology/webcast>",
                ]:
                    continue
                dbpediagen[x][i][3] = dbpediagen[x][i][3][1:]
            if cleaning_rules(dbpediagen[x][i][1], dbpediagen[x][i][3]):
                continue
            if "<http://dbpedia.org/resource/List_of_" in dbpediagen[x][i][0][0]:
                continue
            if dbpediagen[x][i][1] not in stat:
                stat[dbpediagen[x][i][1]] = 0
            if (
                stat[dbpediagen[x][i][1]] < 10
                and stat[dbpediagen[x][i][1]] < maxsample[dbpediagen[x][i][1]]
                and dbpediagen[x][i][2] != ""
                and dbpediagen[x][i][3].lower() not in dbpediagen[x][i][2].lower()
            ):
                output[x] += [dbpediagen[x][i]]
                stat[dbpediagen[x][i][1]] += 1
        print(x, sum([1 for a in stat if stat[a] > 0]), sum([stat[a] for a in stat]))

    for x in ["head", "torso", "tail"]:
        for i in range(len(output[x])):
            output[x][i][2] = (
                output[x][i][2].replace(" the the ", " the ").replace(" the The ", " the ")
            )
            if output[x][i][2].endswith(")?"):
                a = output[x][i][2].split("(")
                if len(a) > 1:
                    l = "(".join(a[:-1])
                    r = a[-1][:-2]
                    if " " + r.lower() + " " in l.lower():
                        output[x][i][2] = l + "?"

    for x in ["head", "torso", "tail"]:
        random.shuffle(output[x])

    with open(os.path.join(working_dir, "head_to_tail_dbpedia.json"), "w", encoding="utf8") as f:
        json.dump(output, f, indent=1, ensure_ascii=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--kg-dir", type=str, default="./")
    parser.add_argument("--working-dir", type=str, default="./")
    args = parser.parse_args()
    
    main(args.kg_dir, args.working_dir)
