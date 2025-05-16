from otree.api import *
import random
import math

doc = """
Игра моделирует гонку технологий, в которой игроки могут выбирать инвестировать в чужую технологию вместо своей.
"""

from tech_race_game import C
 
class C(BaseConstants):
    NAME_IN_URL = 'tech_race_game_copy1'
    PLAYERS_PER_GROUP = C.PLAYERS_PER_GROUP
    TECHNOLOGIES = [i for i in range(1,PLAYERS_PER_GROUP+1)]
    T_MAX = C.T_MAX  # Максимальное количество периодов
    NUM_ROUNDS = T_MAX

    # Параметры игры
    ALPHA = C.ALPHA  # Параметр для функции вероятности
    L = C.L     # Целевой уровень для победы
    V = C.V  # Выигрыш за успешное вложение
    V_NATIVE = C.V_NATIVE  # Выигрыш за победу родной технологии
    # RHO = 0.1  # Ставка дисконтирования

    prob_values_ks = [k for k in range(1, PLAYERS_PER_GROUP + 1)]
    prob_values = []
    for k in range(1, PLAYERS_PER_GROUP + 1):
        prob_values.append(round((k / PLAYERS_PER_GROUP) ** ALPHA,2))
    

class Subsession(BaseSubsession):
    def creating_session(subsession):
        subsession.group_randomly()


class Group(BaseGroup):
    game_continues = models.BooleanField(initial=True)
    max_level = models.IntegerField()


class Player(BasePlayer):
    tech_choice = models.IntegerField( 
        initial=0,
        label="Выберите номер технологии для инвестиции в текущем раунде:",
        choices=C.TECHNOLOGIES,
        widget=widgets.RadioSelect
    )
    
    tech_level = models.IntegerField(initial=0) # Уровень технологии игрока в раунде
    current_investments = models.IntegerField(initial=0) # Количество выбравших технологию игрока в раунде
    level_up = models.BooleanField(initial=False) # Индикатор продвижения технологии



# FUNCTIONS




# PAGES
class ShuffleWaitPage(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession):
        if subsession.round_number == 1:
            subsession.group_randomly()
        else:
            subsession.group_like_round(1)


class Instruction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class CheckStatusWaitPage(WaitPage):
    title_text = 'Ожидайте'
    body_text = 'Проверка статуса игры'

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
    title_text = 'Ожидайте'
    body_text = 'Другие игроки принимают решение'
    
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
            group.game_continues = group.max_level < C.L and group.round_number != C.T_MAX
            if not group.game_continues and group.in_round(group.round_number - 1).game_continues:
                winners = []
                for p in group.get_players():
                    if p.tech_level == group.max_level:
                        winners.append(p)
                for w in winners:
                    w.payoff += C.V_NATIVE
                    for p in group.get_players():
                        for p_tmp in p.in_all_rounds():
                            if p_tmp.tech_choice == w.id_in_group and w.in_round(p_tmp.round_number).level_up:
                                p.payoff += C.V #* math.exp(-C.RHO * p_tmp.round_number) # Дисконтирование отключено  


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return not player.group.game_continues and player.in_round(player.round_number - 1).group.game_continues
    
    @staticmethod
    def vars_for_template(player: Player):
        winners = []
        for p in player.group.get_players():
            if p.tech_level == p.group.max_level:
                winners.append(p)
        return {
            'winners': winners,
            'last_winner': winners[-1],
            'players': player.group.get_players()
        }


class FinalWaitPage(WaitPage):
    wait_for_all_groups = True
    @staticmethod
    def is_displayed(player: Player):
        return not player.group.game_continues and player.in_round(player.round_number - 1).group.game_continues




page_sequence = [
    ShuffleWaitPage,
    Instruction, 
    CheckStatusWaitPage, 
    DecisionPage, 
    DecisionWaitPage,
    Results,
    FinalWaitPage]        
