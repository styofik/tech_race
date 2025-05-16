from otree.api import *


doc = """
Авторизация участников
"""


class C(BaseConstants):
    NAME_IN_URL = 'welcomeapp'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    label = models.StringField(
        label='Ваша фамилия и имя:'
    )


# PAGES
class WelcomePage(Page):
    form_model = 'player'
    form_fields = ['label']

    @staticmethod
    def is_displayed(player: Player):
        return player.subsession.round_number == 1
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.label = player.label


page_sequence = [WelcomePage]
