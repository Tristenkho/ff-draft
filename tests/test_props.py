import unittest

from season import props


RATES = {'fd_per_reception': {'WR': 0.597, 'TE': 0.511, 'RB': 0.325},
         'fd_per_carry': {'RB': 0.224, 'QB': 0.344, 'WR': 0.291}}


def book(market, player, point, over, under):
    return {'key': market, 'outcomes': [
        {'name': 'Over', 'description': player, 'point': point, 'price': over},
        {'name': 'Under', 'description': player, 'point': point, 'price': under}]}


class OddsMathTests(unittest.TestCase):
    def test_american_odds_convert_to_implied_probability(self):
        self.assertAlmostEqual(props.american_to_probability(-110), 0.5238, places=3)
        self.assertAlmostEqual(props.american_to_probability(100), 0.5, places=6)
        self.assertAlmostEqual(props.american_to_probability(150), 0.4, places=6)

    def test_zero_price_is_rejected(self):
        with self.assertRaises(ValueError):
            props.american_to_probability(0)

    def test_devig_removes_the_book_margin(self):
        fair = props.devig([-110, -110])
        self.assertAlmostEqual(sum(fair), 1.0, places=9)
        self.assertAlmostEqual(fair[0], 0.5, places=9)

    def test_devig_keeps_an_asymmetric_market_ordered(self):
        fair = props.devig([-200, 160])
        self.assertAlmostEqual(sum(fair), 1.0, places=9)
        self.assertGreater(fair[0], fair[1])

    def test_even_market_returns_the_posted_line(self):
        self.assertAlmostEqual(props.expected_over_under(7.5, 0.5, 2.2), 7.5, places=9)

    def test_over_favoured_market_shifts_the_mean_up(self):
        mean = props.expected_over_under(7.5, 0.55, 2.2)
        self.assertGreater(mean, 7.5)
        self.assertLess(mean - 7.5, 0.4)  # small correction near a coin flip

    def test_under_favoured_market_shifts_the_mean_down(self):
        self.assertLess(props.expected_over_under(7.5, 0.42, 2.2), 7.5)


class NameMatchingTests(unittest.TestCase):
    def test_suffixes_and_punctuation_are_folded(self):
        self.assertEqual(props.normalize("Ja'Marr Chase"), 'jamarr chase')
        self.assertEqual(props.normalize('Luther Burden III'), props.normalize('Luther Burden'))
        self.assertEqual(props.normalize('Aaron Jones Sr.'), props.normalize('Aaron Jones'))

    def test_accents_are_folded(self):
        self.assertEqual(props.normalize('Amon-Ra St. Brown'), props.normalize('Amon Ra St Brown'))


class ScoringConversionTests(unittest.TestCase):
    def test_receiver_line_converts_to_league_points(self):
        lines = {'player_receptions': {'point': 7.5, 'over': 0.5},
                 'player_reception_yds': {'point': 87.5, 'over': 0.5},
                 'player_anytime_td': {'yes': 0.55}}
        result = props.project('WR', lines, RATES)
        # 8.75 yards + 3.75 receptions + 2.24 first downs + 3.30 touchdown
        self.assertAlmostEqual(result['points'], 18.04, places=2)

    def test_first_down_bonus_uses_the_position_rate(self):
        lines = {'player_receptions': {'point': 6.0, 'over': 0.5}}
        wr = props.project('WR', lines, RATES)['points']
        te = props.project('TE', lines, RATES)['points']
        self.assertGreater(wr, te)  # WR converts receptions to first downs more often
        self.assertAlmostEqual(wr - te, 6.0 * (0.597 - 0.511) * 0.5, places=2)

    def test_missing_first_down_rate_is_reported_not_silently_zero(self):
        result = props.project('K', {'player_receptions': {'point': 2.0, 'over': 0.5}}, RATES)
        self.assertTrue(any('first-down rate' in note for note in result['unmodeled']))

    def test_quarterback_flags_unmodeled_passing_first_downs(self):
        lines = {'player_pass_yds': {'point': 250.0, 'over': 0.5},
                 'player_pass_tds': {'point': 1.5, 'over': 0.5},
                 'player_pass_interceptions': {'point': 0.5, 'over': 0.5}}
        result = props.project('QB', lines, RATES)
        # 10.0 passing yards + 6.0 touchdowns - 1.0 interception
        self.assertAlmostEqual(result['points'], 15.0, places=2)
        self.assertTrue(any('Passing first downs' in note for note in result['unmodeled']))

    def test_one_sided_market_contributes_nothing(self):
        result = props.project('WR', {'player_receptions': {'point': 5.0, 'over': None}}, RATES)
        self.assertEqual(result['points'], 0.0)
        self.assertEqual(result['breakdown'], [])

    def test_rushing_first_downs_need_an_attempts_line(self):
        yards_only = props.project('RB', {'player_rush_yds': {'point': 60.0, 'over': 0.5}}, RATES)
        self.assertAlmostEqual(yards_only['points'], 6.0, places=2)
        self.assertTrue(any('rush-attempt' in note for note in yards_only['unmodeled']))
        with_carries = props.project('RB', {'player_rush_yds': {'point': 60.0, 'over': 0.5},
                                            'player_rush_attempts': {'point': 14.0, 'over': 0.5}}, RATES)
        self.assertAlmostEqual(with_carries['points'], 6.0 + 14.0 * 0.224 * 0.25, places=2)


class EventParsingTests(unittest.TestCase):
    def test_two_books_are_averaged_after_each_is_devigged(self):
        event = {'bookmakers': [
            {'markets': [book('player_receptions', 'Ja\'Marr Chase', 7.5, -110, -110)]},
            {'markets': [book('player_receptions', 'Ja\'Marr Chase', 7.5, -130, 110)]}]}
        parsed = props.parse_event(event)
        entry = parsed['jamarr chase']['player_receptions']
        self.assertEqual(entry['books'], 2)
        self.assertEqual(entry['point'], 7.5)
        self.assertGreater(entry['over'], 0.5)  # second book leans over
        self.assertLess(entry['over'], 0.57)

    def test_one_sided_quote_is_dropped(self):
        event = {'bookmakers': [{'markets': [{'key': 'player_receptions', 'outcomes': [
            {'name': 'Over', 'description': 'Ja\'Marr Chase', 'point': 7.5, 'price': -110}]}]}]}
        self.assertEqual(props.parse_event(event), {})

    def test_unknown_markets_are_ignored(self):
        event = {'bookmakers': [{'markets': [book('player_tackles', 'Someone Else', 5.5, -110, -110)]}]}
        self.assertEqual(props.parse_event(event), {})

    def test_anytime_touchdown_is_devigged_as_yes_no(self):
        event = {'bookmakers': [{'markets': [{'key': 'player_anytime_td', 'outcomes': [
            {'name': 'Yes', 'description': 'Bucky Irving', 'point': None, 'price': -110},
            {'name': 'No', 'description': 'Bucky Irving', 'point': None, 'price': -110}]}]}]}
        parsed = props.parse_event(event)
        self.assertAlmostEqual(parsed['bucky irving']['player_anytime_td']['yes'], 0.5, places=9)


if __name__ == '__main__':
    unittest.main()
