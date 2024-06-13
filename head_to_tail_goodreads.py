# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import gzip
import json
import os
import random


def ascii_ratio(x):
    c = 0
    for a in x:
        if a.isascii():
            c += 1
    return c / len(x) if x != "" else 0

def main(kg_dir, working_dir):
    goodreads_entity_year_freq = {}
    goodreads_entity_htt_l = []
    goodreads_entity_ratings = {}

    with gzip.open(os.path.join(kg_dir, "goodreads_books.json.gz"), "rb") as f:
        l = f.readline()
        while l:
            l = json.loads(l.decode())
            title = l["title"].lower().strip()
            title_year = title + "@" + l["publication_year"]
            if title_year not in goodreads_entity_year_freq:
                goodreads_entity_year_freq[title_year] = 0
            goodreads_entity_year_freq[title_year] += 1
            if title not in goodreads_entity_ratings:
                goodreads_entity_ratings[title] = 0
            goodreads_entity_ratings[title] += (
                int(l["ratings_count"]) if l["ratings_count"].isdigit() else 0
            )
            l = f.readline()

    for x in goodreads_entity_ratings:
        goodreads_entity_htt_l.append(goodreads_entity_ratings[x])

    goodreads_entity_htt_l.sort()
    goodreads_entity_htt_l_s = [0]
    for i in range(len(goodreads_entity_htt_l)):
        goodreads_entity_htt_l_s.append(
            goodreads_entity_htt_l_s[i] + goodreads_entity_htt_l[i]
        )
    goodreads_entity_co1 = None
    goodreads_entity_co2 = None
    for i in range(len(goodreads_entity_htt_l)):
        if (
            goodreads_entity_co1 is None
            and (goodreads_entity_htt_l_s[i + 1] - goodreads_entity_htt_l_s[0])
            / (
                goodreads_entity_htt_l_s[len(goodreads_entity_htt_l)]
                - goodreads_entity_htt_l_s[0]
            )
            >= 1.0 / 3.0
        ):
            goodreads_entity_co1 = i
        if (
            goodreads_entity_co2 is None
            and (goodreads_entity_htt_l_s[i + 1] - goodreads_entity_htt_l_s[0])
            / (
                goodreads_entity_htt_l_s[len(goodreads_entity_htt_l)]
                - goodreads_entity_htt_l_s[0]
            )
            >= 2.0 / 3.0
        ):
            goodreads_entity_co2 = i

    goodreads_author = {}
    with gzip.open(os.path.join(kg_dir, "goodreads_book_authors.json.gz"), "rb") as f:
        l = f.readline()
        while l:
            l = json.loads(l.decode())
            goodreads_author[l["author_id"]] = l["name"]
            l = f.readline()

    random.seed(42)
    goodreads_entity_head = []
    goodreads_entity_torso = []
    goodreads_entity_tail = []

    with gzip.open(os.path.join(kg_dir, "goodreads_books.json.gz"), "rb") as f:
        l = f.readline()
        while l:
            l = json.loads(l.decode())
            title = l["title"].lower().strip()
            ratingcnt = goodreads_entity_ratings[title]
            if (
                ratingcnt > goodreads_entity_htt_l[goodreads_entity_co1]
                or random.random() < 0.01
            ):
                if ratingcnt <= goodreads_entity_htt_l[goodreads_entity_co1]:
                    goodreads_entity_tail.append(l)
                elif ratingcnt <= goodreads_entity_htt_l[goodreads_entity_co2]:
                    goodreads_entity_torso.append(l)
                else:
                    goodreads_entity_head.append(l)
            l = f.readline()

    random.shuffle(goodreads_entity_head)
    random.shuffle(goodreads_entity_torso)
    random.shuffle(goodreads_entity_tail)

    goodreadsgen = {"head": [], "torso": [], "tail": []}
    goodreadssplit = {
        "head": goodreads_entity_head,
        "torso": goodreads_entity_torso,
        "tail": goodreads_entity_tail,
    }
    for x in ["head", "torso", "tail"]:
        count = [0, 0, 0, 0]
        for i in range(len(goodreadssplit[x])):
            l = goodreadssplit[x][i]
            title = l["title"].lower().strip()
            title_year = l["title"].lower().strip() + "@" + l["publication_year"]
            if (
                count[0] < 2000
                and l["title"].strip() != ""
                and l["publisher"].strip() != ""
                and goodreads_entity_year_freq[title_year] == 1
                and l["publication_year"] != ""
            ):
                assert l["url"] != ""
                if (
                    ascii_ratio(title) > 0.6
                    and ascii_ratio(l["publisher"]) > 0.6
                    and int(l["publication_year"]) <= 2015
                ):
                    q = "Who is the publisher of %s (published in %s)?" % (
                        l["title"],
                        l["publication_year"],
                    )
                    a = l["publisher"]
                    goodreadsgen[x].append([l["url"], "goodreads-book-0", q, a])
                    count[0] += 1
            if (
                count[1] < 2000
                and l["authors"] is not None
                and len(l["authors"]) > 0
                and goodreads_entity_year_freq[title_year] == 1
                and l["publication_year"] != ""
            ):
                if (
                    ascii_ratio(title) > 0.6
                    and max(
                        [
                            ascii_ratio(goodreads_author[l["authors"][j]["author_id"]])
                            for j in range(len(l["authors"]))
                        ]
                    )
                    > 0.6
                    and int(l["publication_year"]) <= 2015
                ):
                    q = "Who authored %s (published in %s)?" % (
                        l["title"],
                        l["publication_year"],
                    )
                    a = []
                    for j in range(len(l["authors"])):
                        a.append(goodreads_author[l["authors"][j]["author_id"]])
                    goodreadsgen[x].append([l["url"], "goodreads-book-1", q, a])
                    count[1] += 1
            if (
                count[2] < 2000
                and l["isbn13"] != ""
                and goodreads_entity_year_freq[title_year] == 1
                and l["publication_year"] != ""
            ):
                if ascii_ratio(title) > 0.6 and int(l["publication_year"]) <= 2015:
                    q = "What is the ISBN-13 of %s (published in %s)?" % (
                        l["title"],
                        l["publication_year"],
                    )
                    a = l["isbn13"]
                    goodreadsgen[x].append([l["url"], "goodreads-book-2", q, a])
                    count[2] += 1
            if (
                count[3] < 2000
                and l["isbn"] != ""
                and goodreads_entity_year_freq[title_year] == 1
                and l["publication_year"] != ""
            ):
                if ascii_ratio(title) > 0.6 and int(l["publication_year"]) <= 2015:
                    q = "What is the ISBN-10 of %s (published in %s)?" % (
                        l["title"],
                        l["publication_year"],
                    )
                    a = l["isbn"]
                    goodreadsgen[x].append([l["url"], "goodreads-book-3", q, a])
                    count[3] += 1

    output = {"head": [], "torso": [], "tail": []}
    maxsample = {}
    for x in ["head", "torso", "tail"]:
        for i in range(len(goodreadsgen[x])):
            if goodreadsgen[x][i][1] not in maxsample:
                maxsample[goodreadsgen[x][i][1]] = {}
            if x not in maxsample[goodreadsgen[x][i][1]]:
                maxsample[goodreadsgen[x][i][1]][x] = 0
            maxsample[goodreadsgen[x][i][1]][x] += 1
    for x in maxsample:
        maxsample[x] = min(
            maxsample[x]["head"], maxsample[x]["torso"], maxsample[x]["tail"]
        )

    for x in ["head", "torso", "tail"]:
        count = {}
        random.shuffle(goodreadsgen[x])
        for i in range(len(goodreadsgen[x])):
            if goodreadsgen[x][i][1] not in count:
                count[goodreadsgen[x][i][1]] = 0
            if (
                count[goodreadsgen[x][i][1]] < 250
                and count[goodreadsgen[x][i][1]] < maxsample[goodreadsgen[x][i][1]]
            ):
                output[x].append(goodreadsgen[x][i])
                count[goodreadsgen[x][i][1]] += 1
        print(x, count)

    for x in ["head", "torso", "tail"]:
        random.shuffle(output[x])
        print(x, len(output[x]))

    with open(os.path.join(working_dir, "head_to_tail_goodreads.json"), "w", encoding="utf8") as f:
        json.dump(output, f, indent=1, ensure_ascii=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--kg-dir", type=str, default="./")
    parser.add_argument("--working-dir", type=str, default="./")
    args = parser.parse_args()
    
    main(args.kg_dir, args.working_dir)
