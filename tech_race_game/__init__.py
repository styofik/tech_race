from otree.api import *
import random
import math

doc = """
Игра моделирует гонку технологий, в которой игроки могут выбирать инвестировать в чужую технологию вместо своей.
"""


class C(BaseConstants):
    NAME_IN_URL = 'tech_race_game'
    PLAYERS_PER_GROUP = 3
    TECHNOLOGIES = [i for i in range(1,PLAYERS_PER_GROUP+1)]
    T_MAX = 20  # Максимальное количество периодов
    NUM_ROUNDS = T_MAX

    # Параметры игры
    ALPHA = 0.5  # Параметр для функции вероятности
    L = 5  # Целевой уровень для победы
    V = 20  # Выигрыш за успешное вложение
    V_NATIVE = 50  # Выигрыш за победу родной технологии
    RHO = 0.1  # Ставка дисконтирования
    

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    game_continues = models.BooleanField(initial=True)
    max_level = models.IntegerField()


class Player(BasePlayer):
    label = models.StringField(
        label='Ваша фамилия и имя:'
    )
    tech_choice = models.IntegerField( 
        label="Выберите номер технологии для инвестиции в текущем раунде:",
        choices=C.TECHNOLOGIES,
        widget=widgets.RadioSelect
    )
    
    tech_level = models.IntegerField(initial=0) # Уровень технологии игрока в раунде
    current_investments = models.IntegerField(initial=0) # Количество выбравших технологию игрока в раунде
    level_up = models.BooleanField(initial=False) # Индикатор продвижения технологии



# FUNCTIONS




# PAGES
class WelcomePage(Page):
    form_model = 'player'
    form_fields = ['label']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.label = player.label


class Instruction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class CheckStatusWaitPage(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        if group.round_number != 1:
            group.game_continues = group.in_round(group.round_number - 1).game_continues
            for p in group.get_players():
                p.tech_level = p.in_round(p.round_number - 1).tech_level


class DecisionPage(Page):
    form_model = 'player'
    form_fields = ['tech_choice']

    @staticmethod
    def is_displayed(player: Player):
        return player.group.game_continues
    
    @staticmethod
    def vars_for_template(player: Player):
        if player.round_number != 1:
            return {
                'players': player.in_round(player.round_number - 1).group.get_players()
            }
        else:
            return {
                'players': player.group.get_players()
            }


class DecisionWaitPage(WaitPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.group.game_continues
    
    @staticmethod
    def after_all_players_arrive(group: Group):
        if group.game_continues:
            for p in group.get_players():
                p.current_investments = 0
                for p_tmp in group.get_players():
                    if p_tmp.tech_choice == p.id_in_group:
                        p.current_investments += 1
                level_up_prob = (p.current_investments / C.PLAYERS_PER_GROUP) ** C.ALPHA
                p.level_up = random.random() < level_up_prob
                if p.round_number == 1:
                    if p.level_up:
                        p.tech_level = 1
                    else:
                        p.tech_level = 0
                else:
                    if p.level_up:
                        p.tech_level = p.in_round(p.round_number - 1).tech_level + 1
                    else:
                        p.tech_level = p.in_round(p.round_number - 1).tech_level
            group.max_level = max(group.get_players(), key = lambda player: player.tech_level).tech_level
            group.game_continues = group.max_level < C.L
        

class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not player.group.game_continues and player.in_round(player.round_number - 1).group.game_continues
    
    @staticmethod
    def vars_for_template(player: Player):
        winners = []
        for p in player.group.get_players():
            p.participant.payoff = 0
            if p.tech_level == p.group.max_level:
                winners.append(p)
        for w in winners:
            w.participant.payoff += C.V_NATIVE
            for p_tmp in player.in_all_rounds():
                if p_tmp.tech_choice == w.id_in_group and w.in_round(p_tmp.round_number).level_up:
                   player.participant.payoff += C.V * math.exp(-C.RHO * p_tmp.round_number) 
        return {
            'winners': winners,
            'last_winner': winners[-1],
            'players': player.group.get_players()
        }




page_sequence = [
    WelcomePage, 
    Instruction, 
    CheckStatusWaitPage, 
    DecisionPage, 
    DecisionWaitPage, 
    Results]        
