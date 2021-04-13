import numpy as np
import itertools
import os
import pickle

starting_instability = 5
starting_tiers = [5, 0, 0, 0]
tiers_to_beat = [5, 5, 5, 5]

MAX_TIER = 5
MAX_INSTABILITY = 100

target_filename = os.path.join('craft_cache', '_'.join([str(x) for x in tiers_to_beat]) + '.pkl')

# Tier is current tier!
def fracture_chance(instability, tier):
	return (instability + 5 * tier if instability > 0 else 0) / 100

if False and os.path.exists(target_filename):
	with open(target_filename, 'rb') as f:
		print("Loading cache target file")
		expected_payoff, best_actions = pickle.load(f)
else:
	# Do +5 below to account for possibility that itmes go above 5 instability
	expected_payoff = np.zeros((MAX_INSTABILITY+5,) + (MAX_TIER + 1,) * 4)
	best_glyph = np.zeros((MAX_INSTABILITY+5,) + (MAX_TIER + 1,) * 4, dtype=int)
	best_actions = np.empty((MAX_INSTABILITY+5,) + (MAX_TIER + 1,) * 4, dtype='O')
	slices = [slice(None)]
	for tier_to_beat in tiers_to_beat:
		slices.append(slice(tier_to_beat, None))
	expected_payoff[tuple(slices)] = 1

	tier_iterator = range(MAX_TIER, -1, -1)

	for instability in range(MAX_INSTABILITY - 1, -1, -1):
		if instability % 10 == 0:
			print("Solving instability:", instability)
		for tiers in itertools.product(*[tier_iterator] * 4):
			key = (instability,) + tuple(tiers)
			if expected_payoff[key] == 1:
				continue

			best_action = (0, 0, "Nothing")
			for upgrade_position, tier in enumerate(tiers):
				if tier == MAX_TIER:
					continue
				new_tiers = list(tiers)
				new_tiers[upgrade_position] += 1
				fchance = fracture_chance(instability, tier)
				guardian_payoff = max(1 - max(fchance - 0.25, 0), 0) * expected_payoff[(instability+5,) + tuple(new_tiers)]
				stability_payoff = max(1 - fchance, 0) * np.mean(expected_payoff[(slice(instability+2, instability+6),) + tuple(new_tiers)])
				guardian_action = (guardian_payoff, 1, f'G {upgrade_position}')
				stability_action = (stability_payoff, 0, f'S {upgrade_position}')
				best_action = max(best_action, guardian_action)
				best_action = max(best_action, stability_action)

			if best_action[2][0] == 'S':
				best_glyph[key] = 1
			expected_payoff[key], _, best_actions[key] = best_action

	with open(target_filename, 'wb') as f:
		print("Storing cache target file")
		pickle.dump((expected_payoff, best_actions), f)

action_abbrev_to_action = {'G': 'Guardian', 'S': 'Stability'}

print("\nYou are trying to get tiers:", tiers_to_beat)

cur_key = (starting_instability,) + tuple(starting_tiers)
while True:
	instability = cur_key[0]
	tiers = list(cur_key[1:])
	if expected_payoff[cur_key] == 1:
		print("Craft complete!")
		break
	print("\nCurrent instability:", instability, '| Current tiers:', tiers)
	print("Current chance of completion:", expected_payoff[cur_key])
	best_action = best_actions[cur_key]
	action_type, position = best_action.split(' ')
	position = int(position)
	fchance = fracture_chance(instability, tiers[position])
	if action_type == 'G':
		fchance = max(0, fchance - 0.25)
	fchance = int(fchance * 100)
	print('Best action:', action_abbrev_to_action[action_type], 'mod at position', position, f'| Fracture {fchance}%')

	if action_type == 'S':
		s = input("Final instability: ")
		if s in ('q', 'Q', 'n', 'N'):
			break
		instability = int(s)
	else:
		s = input('Success? (y/n) ')
		if s in ('y', 'Y'):
			instability += 5
		else:
			break

	new_key = list(cur_key)
	new_key[0] = instability
	new_key[position + 1] += 1
	cur_key = tuple(new_key)