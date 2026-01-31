from __future__ import annotations

import os

from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union

import tcod.event
from tcod import libtcodpy

import actions
from actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction
)
import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.KeySym.UP: (0, -1),
    tcod.event.KeySym.DOWN: (0, 1),
    tcod.event.KeySym.LEFT: (-1, 0),
    tcod.event.KeySym.RIGHT: (1, 0),
    tcod.event.KeySym.HOME: (-1, -1),
    tcod.event.KeySym.END: (-1, 1),
    tcod.event.KeySym.PAGEUP: (1, -1),
    tcod.event.KeySym.PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.KeySym.KP_1: (-1, 1),
    tcod.event.KeySym.KP_2: (0, 1),
    tcod.event.KeySym.KP_3: (1, 1),
    tcod.event.KeySym.KP_4: (-1, 0),
    tcod.event.KeySym.KP_6: (1, 0),
    tcod.event.KeySym.KP_7: (-1, -1),
    tcod.event.KeySym.KP_8: (0, -1),
    tcod.event.KeySym.KP_9: (1, -1),
    # Vi keys. エラー回避用にK_hをKeySym.hの書き方に変更しました →ダメだったので全カットとします
    # part7にて大文字にすれば入力可能と判明したため8文字すべて大文字に変更   
    tcod.event.KeySym.H: (-1, 0),
    tcod.event.KeySym.J: (0, 1),
    tcod.event.KeySym.K: (0, -1),
    tcod.event.KeySym.L: (1, 0),
    tcod.event.KeySym.Y: (-1, -1),
    tcod.event.KeySym.U: (1, -1),
    tcod.event.KeySym.B: (-1, 1),
    tcod.event.KeySym.N: (1, 1),
}

WAIT_KEYS = {
    tcod.event.KeySym.PERIOD,
    tcod.event.KeySym.KP_5,
    tcod.event.KeySym.CLEAR,
}

CONFIRM_KEYS = {
    tcod.event.KeySym.RETURN,
    tcod.event.KeySym.KP_ENTER,
}


ActionOrHandler = Union[Action, "BaseEventHandler"]
"""An event handler return value which can trigger an action or switch active handlers.

If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # --- デバッグ記録用 ---
            self.engine.turn_count += 1 
            # ---- ここまで デバッグ記録用----
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            # === ドラゴン討伐クリアED実装 ===
            if getattr(self.engine, "game_cleared", False):
                import score_utils
                # クリア時もスコアを保存
                # score_utils.save_detailed_score(self.engine, self.engine.player.gold)
                saved_data = score_utils.save_detailed_score(
                    self.engine,
                    self.engine.player.gold,
                    is_cleared=True
                )
                return GameClearEventHandler(self.engine, latest_score=saved_data)
            # === ここまで追加 ドラゴン討伐クリアED実装 ===
            return MainGameEventHandler(self.engine)  # Return to the main handler.

            # 通常時は自分自身（現在のハンドラ）を返す、推奨されたが採用せず
            # return self
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """Handle actions returned from event methods.

        Returns True if the action will advance a turn.
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        x = int(event.tile.x)   #part7から離れたオリジナルの変更
        y = int(event.tile.y)   #part7から離れたオリジナルの変更
        
        if self.engine.game_map.in_bounds(x, y):    #part7から離れたオリジナルの変更
            self.engine.mouse_location = x, y       #part7から離れたオリジナルの変更

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)


class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        if event.sym in {  # Ignore modifier keys.
            tcod.event.KeySym.LSHIFT,
            tcod.event.KeySym.RSHIFT,
            tcod.event.KeySym.LCTRL,
            tcod.event.KeySym.RCTRL,
            tcod.event.KeySym.LALT,
            tcod.event.KeySym.RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """By default any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Information"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=7,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(
            x=x + 1, y=y + 1, string=f"Level: {self.engine.player.level.current_level}"
        )
        console.print(
            x=x + 1, y=y + 2, string=f"XP: {self.engine.player.level.current_xp}"
        )
        console.print(
            x=x + 1,
            y=y + 3,
            string=f"XP for next Level: {self.engine.player.level.experience_to_next_level}",
        )

        console.print(
            x=x + 1, y=y + 4, string=f"Attack: {self.engine.player.fighter.power}"
        )
        console.print(
            x=x + 1, y=y + 5, string=f"Defense: {self.engine.player.fighter.defense}"
        )


class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        console.draw_frame(
            x=x,
            y=0,
            width=35,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=1, string="Congratulations! You level up!")
        console.print(x=x + 1, y=2, string="Select an attribute to increase.")

        console.print(
            x=x + 1,
            y=4,
            string=f"a) Constitution (+20 HP, from {self.engine.player.fighter.max_hp})",
        )
        console.print(
            x=x + 1,
            y=5,
            string=f"b) Strength (+1 attack, from {self.engine.player.fighter.power})",
        )
        console.print(
            x=x + 1,
            y=6,
            string=f"c) Agility (+1 defense, from {self.engine.player.fighter.defense})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.A    #KeySym表記へ変更、part11オリジナル修正

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp()
            elif index == 1:
                player.level.increase_power()
            else:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid entry.", color.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None


class InventoryEventHandler(AskUserEventHandler):
    """This handler lets the user select an item.

    What happens then depends on the subclass.
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """Render an inventory menu, which displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        from components.consumable import HealingConsumable # ポーション緑文字表示用

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                
                is_equipped = self.engine.player.equipment.item_is_equipped(item)

                item_string = f"({item_key}) {item.name}"

                if is_equipped:
                    item_string = f"{item_string} (E)"

                # --- ここから追加：色の判定 ---
                # デフォルトは白
                text_color = (255, 255, 255) 
                
                # アイテムが HealingConsumable を持っていれば緑色にする
                if isinstance(item.consumable, HealingConsumable):
                    text_color = (0, 220, 0) # 緑色
                # --- ここまでポーション緑文字表示修正 ---

                # fg=text_color を追加して描画
                console.print(x + 1, y + i + 1, item_string, fg=text_color)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.A   # part8オリジナル修正

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        if item.consumable:
            # Return the action for the selected item.
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return actions.EquipAction(self.engine.player, item)
        else:
            return None

class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item."""

    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop this item."""
        return actions.DropItem(self.engine.player, item)


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = color.white
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.Modifier.LSHIFT | tcod.event.Modifier.RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.Modifier.LCTRL | tcod.event.Modifier.RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.Modifier.LALT | tcod.event.Modifier.RALT):   # ALTが機能していないが、静観
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()


class LookHandler(SelectIndexHandler):
    """Lets the player look around using the keyboard."""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Return to main handler."""
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        player = self.engine.player

        if key == tcod.event.KeySym.PERIOD and modifier & (
            tcod.event.Modifier.LSHIFT | tcod.event.Modifier.RSHIFT
        ):
            return actions.TakeStairsAction(player)


        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)
        elif key in WAIT_KEYS:
            action = WaitAction(player)

        elif key == tcod.event.KeySym.ESCAPE:
            raise SystemExit()

        elif key == tcod.event.KeySym.V:    #tcod.event.KeySym.vを大文字Vに変えた、その上でKeySym.V表記に変更
            return HistoryViewer(self.engine)

        elif key == tcod.event.KeySym.G:    # part8で追加、キー表記モダンに変更
            action = PickupAction(player)
        
        elif key == tcod.event.KeySym.I:    # part8で追加、キー表記モダンに変更
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.KeySym.D:    # part8で追加、キー表記モダンに変更
            return InventoryDropHandler(self.engine)
        elif key == tcod.event.KeySym.C:    # part11で追加、キー表記モダンに変更    #このブロックにキーを足せば各イベントを呼び出せる
            return CharacterScreenEventHandler(self.engine)
        elif key == tcod.event.KeySym.SLASH:     # part9で追加、起動確認済み
            return LookHandler(self.engine)


        # No valid key was pressed
        return action


class GameOverEventHandler(EventHandler):
        # ---ハイスコア表示用修正---
    def __init__(self, engine: Engine):
        super().__init__(engine)
        # ゲームオーバーになった瞬間に保存
        import score_utils
        # score_utils.save_score(
        #     gold=engine.player.gold,
        #     floor=engine.game_world.current_floor,
        #     level=engine.player.level.current_level
        # )

        self.saved_score_data = score_utils.save_detailed_score(
            engine, engine.player.gold, is_cleared=False
        )

    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()
    
    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        # if event.sym == tcod.event.KeySym.ESCAPE:
        #     self.on_quit()

        # # --- ここから追加 ---
        # elif event.sym == tcod.event.KeySym.n:
        #     # ニューゲーム（現在のセーブデータを消して最初から）
        #     if os.path.exists("savegame.sav"):
        #         os.remove("savegame.sav")
        #     # main.py のループを抜けて再起動させるために SystemExit を利用するか、
        #     # 簡便な方法として main.py の冒頭に戻るロジックを組みます
        #     # ここでは一番簡単な「メインメニューに戻る」の実装例を紹介します
        #     import setup_game
        #     self.engine.event_handler = setup_game.MainMenu() 
            
        # elif event.sym == tcod.event.KeySym.m:
        #     # メインメニューに戻る
        #     import setup_game
        #     self.engine.event_handler = setup_game.MainMenu()
        # # --- ここまで追加 ---

        # KeySym.ESCAPE に統一
        if event.sym == tcod.event.KeySym.ESCAPE:
            raise SystemExit()

        # ここを KeySym.N にする（これで小文字のn入力にも反応します）
        elif event.sym == tcod.event.KeySym.N:
            import setup_game
            
            if os.path.exists("savegame.sav"):
                os.remove("savegame.sav")
            
            # メインメニューへ戻る
            return setup_game.MainMenu()
        
        elif event.sym == tcod.event.KeySym.M:
            # メインメニューに戻る
            import setup_game
            return setup_game.MainMenu()
        
        elif event.sym == tcod.event.KeySym.R:

            return RankingEventHandler(self.engine, latest_score=self.saved_score_data)
        
        return None # 何も起きなかった場合
    
    # def on_render(self, console: tcod.console.Console) -> None:
    #     super().on_render(console)  # 既存の画面（マップ等）を描画

    #     # 画面の中央の座標を計算
    #     x = console.width // 2
    #     y = console.height // 2

    #     # メッセージを表示
    #     # alignment=tcod.CENTER を使うと、指定した座標がテキストの中心になります
    #     console.print(
    #         x,
    #         y + 4,  # "Game Over" の文字と重ならないよう、少し下にずらす
    #         "Press [N] for New Game / [ESCAPE] to Quit",
    #         fg=(255, 255, 255),  # 白色
    #         bg=(0, 0, 0),        # 背景を黒にして読みやすくする
    #         alignment=tcod.CENTER,
    #     )



class GameClearEventHandler(EventHandler):
    # latest_score を引数で受け取れるようにする
    def __init__(self, engine: Engine, latest_score: dict):
        super().__init__(engine)
        # ここでは保存せず、受け取ったデータを利用する
        self.saved_score_data = latest_score
    
    """ゲームクリア時に表示される画面"""
    def on_render(self, console: tcod.console.Console) -> None:
        super().on_render(console)
        
        # 画面中央にクリアメッセージを表示
        console.print(
            console.width // 2,
            console.height // 2,
            "--- VICTORY ---",
            fg=(255, 255, 0),
            alignment=tcod.CENTER,
        )
        console.print(
            console.width // 2,
            console.height // 2 + 2,
            "You have defeated the Dragon and cleared the game!",
            alignment=tcod.CENTER,
        )
        # 最終スコアを表示
        final_gold = self.saved_score_data.get("gold", 0)
        console.print(
            console.width // 2,
            console.height // 2 + 4,
            f"Final Wealth: {final_gold}G",
            fg=(255, 215, 0),
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        # 何かキーを押したらメインメニュー（またはランキング）へ
        return RankingEventHandler(self.engine, latest_score=self.saved_score_data)


CURSOR_Y_KEYS = {
    tcod.event.KeySym.UP: -1,
    tcod.event.KeySym.DOWN: 1,
    tcod.event.KeySym.PAGEUP: -10,
    tcod.event.KeySym.PAGEDOWN: 10,
}


class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.console.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment=libtcodpy.CENTER
        )

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.KeySym.HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.KeySym.END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return MainGameEventHandler(self.engine)
        return None


class RankingEventHandler(BaseEventHandler):
    def __init__(self, engine: Optional[Engine] = None, latest_score: Optional[dict] = None):
        self.engine = engine
        self.latest_score = latest_score # 最新のスコアを保持

    def on_render(self, console: tcod.console.Console) -> None:
        import score_utils
        scores = score_utils.load_scores()

        # 画面中央に少し小さめの枠を作る例
        margin = 4
        # 引数名を x, y に修正します
        console.draw_frame(
            x=margin,
            y=margin,
            width=console.width- (margin * 2), 
            height=console.height- (margin * 2),
            title=" HIGH SCORES ", 
            clear=True, 
            fg=(255, 255, 255), 
            bg=(0, 0, 0)
        )

        # console.print(x=5, y=5, string="RANK    GOLD    FLOOR  LEVEL", fg=(255, 255, 0))
        console.print(x=5, y=5, 
                      string=" RANK    GOLD   LEVEL  FLOOR   EXP    DEALT TAKEN   HP ATK DEF  TURN", 
                      fg=(255, 255, 0))
        # console.print(x=header_x, y=margin + 2, string="RANK    GOLD    TURN    LV   FL", fg=(255, 255, 0))
        for i, score in enumerate(scores):
            y = 7 + i
            
            # --- ここで色を決定 ---
            # もし描画中のスコアが、今回保存した最新スコアと一致したら黄色にする
            if score == self.latest_score:
                text_color = (255, 255, 0)  # 黄色
                rank_prefix = "NEW->"      # 最新だとわかる目印（お好みで）"NEW->"
            else:
                text_color = (255, 255, 255) # 通常は白
                rank_prefix = f"#{i+1:<4}"   #左寄せ4文字の意味(数字+スペース3文字)
            
            # JSONから各値を取り出す（キーが存在しない場合のデフォルト値も設定しておくと安全です）
            gold = score.get("gold", 0)
            level = score.get("level", 1)
            floor = score.get("floor", 1)
            total_exp = score.get("total_exp", 0)
            damage_dealt = score.get("damage_dealt", 0)
            damage_taken = score.get("damage_taken", 0)
            stats = score.get("stats", {})
            max_hp = stats.get("max_hp", 0)
            power = stats.get("power", 0)
            defense = stats.get("defense", 0)
            turns = score.get("turns", 0)

            # 文字列のフォーマットを整えて表示
            # >5 は「5文字分右寄せ」、< は左寄せ
            score_string = (
                f"{rank_prefix} "
                f"{gold:>5}g   "
                f"Lv.{level:>2}  "
                f"{floor:>3}F  "
                f"{total_exp:>5}p  "
                f"{damage_dealt:>4}hp "
                f"{damage_taken:>3}hp  "
                f"{max_hp:>3}  "
                f"{power:>2}  "
                f"{defense:>2}  "
                f"{turns:>4}t "
            )
            console.print(
                x=margin + 2, 
                y=y,
                string=score_string,
                fg=text_color
            )
            
            # -------
            # console.print(
            #     x=margin + 2, y=y,
            #     string=f"{rank_prefix} {score['gold']:>5}g   {score['floor']:>3}F    Lv.{score['level']:>2}",
            #     fg=text_color
            # )

        console.print(
            x=console.width // 2, y=console.height - 4,
            string="Press any key to return", alignment=libtcodpy.CENTER
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        # 何かキーを押したらメインメニュー（または前の画面）に戻る
        import setup_game
        return setup_game.MainMenu()