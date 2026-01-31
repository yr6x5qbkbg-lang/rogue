from __future__ import annotations

import lzma
import pickle
from typing import TYPE_CHECKING
import time    # デバッグ記録用

from tcod.console import Console
from tcod.map import compute_fov

from message_log import MessageLog
import render_functions
import exceptions   # 不可能な行動をengineで無効化する場合に必要、part9オリジナル修正

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap, GameWorld


class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        # ---デバッグ記録用修正---
        self.turn_count = 0
        self.total_exp = 0
        self.total_damage_taken = 0
        self.times_attacked = 0
        self.start_time = time.time() # timeモジュールのインポートが必要
        self.total_damage_dealt = 0
        self.total_rooms = 0
        self.item_bonus_gold = 0
        # ---ここまで デバッグ記録用---

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
               entity.ai.perform()  #この行を削除し下を有効にすれば不可能な行動全て無視する

            """    try:
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass    # AIが不可能な行動をしても、単に無視して次の敵へ part9オリジナル修正
            """

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible
            
    def render(self, console: Console) -> None:
        self.game_map.render(console)

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)

        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47),
        )

        render_functions.render_names_at_mouse_location(
            console=console, x=21, y=44, engine=self
        )

    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)