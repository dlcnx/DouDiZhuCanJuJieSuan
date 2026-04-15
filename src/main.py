import sys
import os
from cards import Cards
from cardMove import CardMove, MoveType
from gameCore import GameCore, calculate_best_action, actionCache, MAX_SCORE, MIN_SCORE

class Colors:
    """ANSI终端颜色常量"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def color_print(text: str, color: str = "", bold: bool = False, end: str = "\n"):
    """带颜色的终端输出"""
    prefix = color
    if bold:
        prefix += Colors.BOLD
    print(f"{prefix}{text}{Colors.RESET}", end=end)

def get_card_move(hand: Cards, last_move: CardMove, prompt: str = "") -> CardMove:
    """从用户输入获取合法出牌

    用户输入牌面字符匹配出牌，按回车表示PASS（若合法），
    输入e退出程序，若匹配多个出牌则让用户选择
    """
    from moveGen import gen_all_moves

    all_possible_moves = gen_all_moves(hand, last_move)
    if not all_possible_moves:
        raise RuntimeError("没有可能的出牌")

    while True:
        if prompt:
            color_print(f"{prompt}: ", Colors.YELLOW, end="")
        move_input = input().strip()

        for c in move_input:
            if c == 'e':
                raise RuntimeError("用户选择退出计算")

        if move_input == "":
            pass_move = CardMove(MoveType.PASS)
            if pass_move in all_possible_moves:
                return pass_move
            color_print("当前不能PASS，请出牌", Colors.RED)
            continue

        card_input = Cards(move_input)

        match_moves = []
        for move in all_possible_moves:
            if move.get_all_cards() == card_input:
                match_moves.append(move)

        if len(match_moves) == 0:
            color_print("无匹配，重新输入", Colors.RED)
            continue
        elif len(match_moves) > 1:
            color_print("匹配多个，选择: ", Colors.YELLOW)
            for i, m in enumerate(match_moves, 1):
                color_print(f"  {i}: {m}", Colors.WHITE)
            choice = int(input())
            if choice < 1 or choice > len(match_moves):
                color_print("无效选择", Colors.RED)
                continue
            return match_moves[choice - 1]
        else:
            return match_moves[0]

def play_one_round():
    """执行一局游戏，返回True继续下一局，False退出"""
    try:
        print()
        color_print("=" * 40, Colors.BLUE)
        color_print("        斗地主残局计算器", Colors.BOLD + Colors.CYAN)
        color_print("=" * 40, Colors.BLUE)
        color_print("提示: 0=10, x=小王, d=大王", Colors.DIM)

        color_print("\n请输入我方手牌: ", Colors.YELLOW, end="")
        ourcards = Cards(input().strip())

        color_print("请输入敌方手牌: ", Colors.YELLOW, end="")
        enemycards = Cards(input().strip())

        color_print("敌方出牌(若我方先出请按回车): ", Colors.YELLOW, end="")
        last_move = get_card_move(enemycards, CardMove(MoveType.INVALID))
        enemycards.remove(last_move.get_all_cards())

        game = GameCore(ourcards, enemycards, last_move)
        enemy_last_display = last_move

        while not game.is_game_over():
            print()
            color_print(f"我: {game.get_our_hand()}\n敌: {game.get_enemy_hand()}", Colors.DIM)

            action = calculate_best_action(game.get_current_status())

            if action.score == MIN_SCORE:
                color_print("\n对方有必胜策略!", Colors.RED + Colors.BOLD)
                return True

            color_print(f">> 我出: {action.move}", Colors.GREEN + Colors.BOLD)
            game.play_card(action.move)
            if action.move.get_type() != MoveType.PASS:
                last_move = action.move
            else:
                last_move = CardMove(MoveType.INVALID)

            if game.is_game_over():
                break

            color_print(f"敌方上次: {enemy_last_display}", Colors.DIM)
            color_print("敌方出牌: ", Colors.YELLOW, end="")
            enemy_move = get_card_move(game.get_enemy_hand(), last_move)
            game.play_card(enemy_move)
            if enemy_move.get_type() == MoveType.PASS:
                last_move = CardMove(MoveType.INVALID)
            else:
                last_move = enemy_move
            enemy_last_display = enemy_move

        print()
        color_print(f"我: {game.get_our_hand()} | 敌: {game.get_enemy_hand()}", Colors.DIM)
        if game.get_our_hand().card_num() == 0:
            color_print("★ 我方胜利! ★", Colors.GREEN + Colors.BOLD)
        else:
            color_print("☆ 敌方胜利 ☆", Colors.RED + Colors.BOLD)

        return True

    except KeyboardInterrupt:
        color_print("\n用户退出", Colors.YELLOW)
        return False
    except Exception as e:
        color_print(f"异常: {e}", Colors.RED)
        return False

def main():
    """主循环，支持多局连续对局"""
    while play_one_round():
        color_print("\n继续? (q退出): ", Colors.YELLOW, end="")
        choice = input().strip().lower()
        if choice == 'q':
            color_print("再见!", Colors.CYAN)
            break
        os.system('cls' if os.name == 'nt' else 'clear')

    color_print("程序结束", Colors.DIM)

if __name__ == "__main__":
    main()
