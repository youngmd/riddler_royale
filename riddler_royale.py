#!/usr/bin/env python3
import sys
import random
import csv

castles = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

best_armies = []
old_armies = []
batch_size = 10000
keep = 100

def read_csv(infile):
    with open(infile, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if not line_count:
                line_count += 1
                continue #skip header
            row['source'] = infile
            row['victories'] = 0
            row['total_score'] = 0
            row['score'] = 0

            total = 0
            for i in castles:
                old_key = 'Castle '+str(i)
                try:
                    row[i] = round(float(row[old_key]))
                except:
                    row[i] = 0
                del row[old_key]
                total += row[i]
            if total <= 100:
                old_armies.append(row)
            else:
                print("Invalid total found, skipping!")
            line_count += 1
        print(f'Processed {line_count} lines.')


def min_frac_dist(total, remainder, min_frac, max_frac):
    return min(remainder, round(total*(min_frac + random.random() * (1 - min_frac))))

def max_frac_dist(total, remainder, min_frac, max_frac):
    return min(remainder, round(random.random() * max_frac * total))

def min_max_dist(total, remainder, min_frac, max_frac):
    return min(remainder, round(total*(min_frac + random.random() * (max_frac - min_frac))))

def random_dist(total, remainder, min_frac, max_frac):
    return min(remainder, round(random.random() * total))


dists = {
    'min': min_frac_dist,
    'max': max_frac_dist,
    'minmax': min_max_dist,
    'random': random_dist
}

def make_dist(soldier_count, min_frac, max_frac, dist):
    _castles = castles.copy()
    random.shuffle(_castles)
    _soldiers = soldier_count
    _army = {'victories': 0, 'total_score': 0, 'score': 0, 'min_frac': min_frac, 'max_frac': max_frac, 'dist':dist, 'source': 'Mine'}

    _dist = dists[dist]

    for x in _castles:
        send_soldiers = _dist(soldier_count, _soldiers, min_frac, max_frac)
        if x < 5 and send_soldiers > 15:
            send_soldiers = 15
        if x < 3 and send_soldiers > 3:
            send_soldiers = 3

        _soldiers -= send_soldiers
        _army[x] = send_soldiers

    if _soldiers:
        _army[x] += _soldiers

    return _army

def do_battle(army1, army2):
    army1['score'] = 0
    army2['score'] = 0

    try:
        for x in castles:
            a1_x = army1[x]
            a2_x = army2[x]
            army1['score'] += x if a1_x > a2_x else 0
            army2['score'] += x if a2_x > a1_x else 0
            if(a1_x == a2_x):
                halfsies = x / 2.0
                army1['score'] += halfsies
                army2['score'] += halfsies

        army1['total_score'] += army1['score']
        army2['total_score'] += army2['score']

        if army1['score'] == army2['score']:
            army1['victories'] += 0.5
            army2['victories'] += 0.5
        elif army1['score'] > army2['score']:
            army1['victories'] += 1
        else:
            army2['victories'] += 1
    except:
        print("Unexpected error:", sys.exc_info()[0])
        print(army1)
        print(army2)
        sys.exit(1)

    return


def rumble(army_list):
    for i in range(len(army_list)):
        for j in range(i + 1, len(army_list)):
            do_battle(army_list[i], army_list[j])


def rambo(army_list, army):
    for i in range(len(army_list)):
        do_battle(army_list[i], army)



def batch_battle(soldier_count, batch_count, min_frac, max_frac, dist, keep):

    armies = []
    for i in range(batch_count):
        army = make_dist(soldier_count, min_frac, max_frac, dist)
        armies.append(army)

    rumble(armies)

    armies.sort(key=lambda x: x['victories'], reverse=True)

    best_armies.extend(armies[0:keep])


def print_army(army):
    line = ''
    for x in castles:
        line += str(army[x]) + '\t'

    line += str(army['victories']) + '\t' + str(army['total_score'])
    print(line)

def write_army(army, outfile):
    f = open(outfile, 'a+')
    line = ''
    for x in castles:
        line += str(army[x]) + ','

    line += str(army['victories']) + ',' + str(army['total_score'])+'\n'
    f.write(line)
    f.close()

print("Reading in old armies")

read_csv('./castle-solutions.csv')
read_csv('./castle-solutions-2.csv')
read_csv('./castle-solutions-3.csv')


candidates = []
winners = []
min_wins = 37

print("Generating max_frac armies")
army_count = 0

winner_file = 'winners.csv'


f = open(winner_file, 'w')
line = ''
for x in castles:
    line += str(x) + ','
line += 'victories,total_score\n'
f.write(line)
f.close()

winner_count = 0
best_ratio = 0
while True:
    army_count += 1
    army = make_dist(100, 0.0, 0.38, 'max')
    test_armies = random.sample(old_armies, 50)
    rambo(test_armies, army)
    if army['victories'] > min_wins:
        candidates.append(army)
        print("%s generated, new candidate found" % (army_count))
        army['victories'] = 0
        rambo(old_armies, army)
        ratio = army['victories'] / (1.0 * len(old_armies))
        best_ratio = max(ratio, best_ratio)
        if ratio > 0.75:
            winner_count += 1
            print("Candidate passed (ratio %s), adding to winners! (%s winners so far)" % (ratio, winner_count))
            write_army(army, winner_file)
        else:
            print("Candidate failed, the search continues (%s winners so far, best ratio is %s)" % (winner_count, best_ratio))

# winners.sort(key=lambda x: x['victories'], reverse=True)
#
# for army in winners:
#     print_army(army)


# print("Generating min_frac armies")
# for i in range(1, 9):
#     min_frac = i * 0.1 + 0.1
#     batch_battle(100, batch_size, min_frac, 0.0, 'min', keep)
#
# print("Generating minmax_frac armies")
# for i in range(1, 9):
#     min_frac = i * 0.1 + 0.1
#     max_frac = min(0.95, min_frac+0.1)
#     batch_battle(100, batch_size, min_frac, max_frac, 'minmax', keep)
#
# print("Generating random armies")
# for i in range(1, 9):
#     batch_battle(100, batch_size, 0.0, 0.0, 'random', keep)
#
# print("Pitting group winners in royal rumble")
# for army in best_armies:
#     army['victories'] = army['total_score'] = 0
#
# rumble(best_armies)
#
# best_armies.sort(key=lambda x: x['victories'], reverse=True)
#
# top100 = best_armies[0:100]
#
# print("Resetting scores")
# for army in top100:
#     army['total_score'] = 0
#     army['victories'] = 0
#
# print("Testing my best armies against past submissions")
# old_armies.extend(top100)
#
# rumble(old_armies)
#
# old_armies.sort(key=lambda x: x['victories'], reverse=True)
#
# old_top10 = old_armies[0:10]
#
# for army in old_top10:
#     line = ''
#     for x in castles:
#         line += str(army[x])+'\t'
#
#     line += str(army['victories']) +'\t'+str(army['total_score']) +'\t'+str(army['source'])
#     print(line)
#
# print("########My Armies######")
# for army in old_armies:
#     if army['source'] != 'Mine':
#         continue
#     line = ''
#     for x in castles:
#         line += str(army[x]) + '\t'
#
#     line += str(army['victories']) + '\t' + str(army['total_score']) + '\t' + str(army['source'])
#     print(line)
#

#     #
# # print(*castles, sep='\t')
# #
# # for army in armies:
# #     line = ''
# #     for x in castles:
# #         line += str(army[x])+'\t'
# #     print(line)
# #
# #
# # for i in range(len(armies)):
# #     for j in range(i+1, len(armies)):
# #         do_battle(armies[i], armies[j])
# #
# # best_army = 0
# # max_score = 0
# # for idx, army in enumerate(armies):
# #     if army['victories'] > max_score:
# #         best_army = idx
# #
# # best_armies.append(best_army)
# print(armies[idx])
