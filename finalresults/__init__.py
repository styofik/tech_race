from otree.api import *


doc = """
Финальные результаты по всем играм
"""


class C(BaseConstants):
    NAME_IN_URL = 'finalresults'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass


# PAGES
class FinalResults(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'players': player.subsession.get_players()
        }


page_sequence = [FinalResults]