import pygame
import sys
import os
import random
import math

# スクリプトのディレクトリをワーキングディレクトリに設定
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 定数設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GAME_WIDTH = 640
GAME_HEIGHT = 480
FPS = 60
TILE_SIZE = 40 # 1マスのサイズ

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COLOR = (50, 50, 255)    # プレイヤー (青)
PLATFORM_COLOR = (100, 100, 100) # 足場 (灰色)
SPIKE_COLOR = (255, 50, 50)      # 障害物 (赤)
KEY_COLOR = (255, 215, 0)   # カギ (黄)
DOOR_COLOR = (0, 200, 0)   # トビラ (緑)
PLAYER_BORDER_COLOR = (255, 255, 255) # プレイヤーの枠の色 (白)
PLATFORM_BORDER_COLOR = (255, 255, 255) # 足場の枠の色 (白)
BOOSTER_COLOR = (50, 255, 50) # ブースターの色 (明るい緑)
GRAVITY_SWITCHER_COLOR = (200, 50, 200) # 重力スイッチの色 (紫)
ARROW_COLOR = (200, 200, 200) # 弓矢 (ライトグレー)
LAUNCHER_COLOR = (150, 50, 50) # 発射台 (茶色/赤茶色)
JUMPPAD_COLOR = (200, 0, 255) # ★ジャンプ台 (紫) を追加

# 物理定数
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 5
# 壁キック用の定数
WALL_JUMP_STRENGTH_Y = -19 # 壁キックの縦方向の強さ
WALL_JUMP_STRENGTH_X = 5 # 壁キックの横方向の強さ（移動速度より大きくする）
WALL_SLIDE_SPEED = 2 # 壁ずり落ちる速度

# 弓矢の発射間隔 (ミリ秒)のランダム範囲を設定
MIN_ARROW_INTERVAL = 500  # 最小間隔 (0.5秒)
MAX_ARROW_INTERVAL = 1500 # 最大間隔 (1.5秒)

# WALL_KICK_HORIZONTAL = 10 # 壁キック時の水平方向の力
# WALL_KICK_VERTICAL = -12  # 壁キック時の垂直方向の力
# PLAYER_SPEED = 5

MOVE_SPEED = 5
MAX_SPEED = 6
ACCELERATION = 0.4
FRICTION_FORCE = 0.2

# ヘルパー関数
def get_angle_from_gravity(direction):
    if direction == "UP":
        return 180
    return 0


# --- ステージの設計図 (Booster 'B' を追加) ---
LEVEL_MAP = [
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", # Y=0
    "P......................................P",
    "P....@...PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", # Y=2 (スタート)
    "P.G..P.................................P", # Y=3 に 'B' を追加
    "PPPPPP...PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", # Y=4
    "P........P.............................P",
    "P..SSSS..P...PPPPPPPPPPPPPPPPPPPPPPPPPPP",
    "P..PPPPP.P...P.........................P",
    "P........P...P...S.S...................P",
    "PPPPPPPPBP...P..PPPPP...PPPPPPPPPPPPPPPP",
    "P............P..........P..............P",
    "P....K.......P..........P..............P", # Y=11 (カギ)
    "PPPPPPPPPPPPPP..........P...PPPPPPPPPPPP",
    "P...............G.......P...P..........P",
    "P.......................P...P..........P",
    "P.......................P...P...SSSS...P",
    "P.......................P...P...PPPP...P",
    "P....PPPPPPPPPPPPPPPPPPPP...P..........P",
    "P....P......................P..........P",
    "P....P...PPPPPPPPPPPPPPPPPPPP..........P",
    "P....P...P.............................P",
    "P....P...P...PPPPPPPPPPPPPPPPPPPPPPPPPPP",
    "P....P...P...P...................D.....P", # Y=21 (ゴール)
    "P....P...P...P..................PPP....P",
    "P....PPPPPPPPP.........................P",
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", # Y=24
]

# --- プレイヤークラス (壁キック機能付き) ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, PLAYER_BORDER_COLOR, self.image.get_rect(), 
                         width=1, border_radius=4)
        
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.on_wall_left = False 
        self.on_wall_right = False 
        self.has_key = False
        
        # 壁キック用のフラグ (0: なし, -1: 左壁, 1: 右壁)
        self.on_wall = 0 
        
        # 壁キック用クールダウン
        self.wall_jump_cooldown = 0
        self.WALL_JUMP_COOLDOWN_FRAMES = 10 # 10フレーム (約0.16秒) 入力を無視
        
        # 現在立っている足場 (ブースター判定用)
        self.standing_on = [] 

        # ジャンプ力と速度の倍率
        self.speed_multiplier = 1.0
        self.jump_multiplier = 1.0

    def update(self, platforms, current_gravity):
        keys = pygame.key.get_pressed()
        
        # --- 1. クールダウン処理 ---
        if self.wall_jump_cooldown > 0:
            self.wall_jump_cooldown -= 1

        # --- 2. 左右の入力 (加速・摩擦ベース) ---
        target_vel_x = 0
        
        # 壁キックのクールダウン中でない場合のみ、左右の入力を受け付ける
        if self.wall_jump_cooldown == 0:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                target_vel_x = -MOVE_SPEED * self.speed_multiplier
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                target_vel_x = MOVE_SPEED * self.speed_multiplier
        
        # 加速/摩擦の計算
        if target_vel_x != 0: # 加速
            self.vel_x += (target_vel_x - self.vel_x) * ACCELERATION
        else: # 摩擦
            self.vel_x *= (1.0 - FRICTION_FORCE)
        
        # 速度制限と停止
        if abs(self.vel_x) < 0.1: self.vel_x = 0
        self.vel_x = max(-MAX_SPEED * self.speed_multiplier, min(self.vel_x, MAX_SPEED * self.speed_multiplier))
        
        # --- 3. Y軸の重力と壁ずり落ち ---
        if not self.on_ground:
            
            # ★--- 修正点 (ここから) ---★
            
            # 壁ずり落ち (重力が下向きの時)
            if self.on_wall != 0 and self.vel_y > 0 and current_gravity == "DOWN":
                 self.vel_y = min(self.vel_y + GRAVITY, WALL_SLIDE_SPEED)
            
            # 壁ずり落ち (重力が上向きの時)
            elif self.on_wall != 0 and self.vel_y < 0 and current_gravity == "UP":
                 # "落下"(上昇)速度を遅くする
                 self.vel_y = max(self.vel_y - GRAVITY, -WALL_SLIDE_SPEED)
            
            # ★--- 修正点 (ここまで) ---★

            # 通常の重力 (壁ずり落ち中でない場合)
            else:
                if current_gravity == "DOWN":
                    self.vel_y += GRAVITY
                elif current_gravity == "UP":
                    self.vel_y -= GRAVITY
                # 最大落下/上昇速度
                self.vel_y = max(-10, min(self.vel_y, 10)) 

        # --- 4. X軸（横）の移動と衝突判定 ---
        self.rect.x += self.vel_x
        hit_list_x = pygame.sprite.spritecollide(self, platforms, False)
        
        # 壁接触フラグをリセット
        self.on_wall = 0 
        self.on_wall_right = False
        self.on_wall_left = False
        
        for platform in hit_list_x:
            if self.vel_x > 0: # 右に移動中
                self.rect.right = platform.rect.left
                self.on_wall_right = True
                self.on_wall = 1 # 右壁
            elif self.vel_x < 0: # 左に移動中
                self.rect.left = platform.rect.right
                self.on_wall_left = True
                self.on_wall = -1 # 左壁
            self.vel_x = 0 # 壁にぶつかったら横速度リセット
        
        # --- 5. Y軸（縦）の移動と衝突判定 ---
        self.rect.y += self.vel_y
        hit_list_y = pygame.sprite.spritecollide(self, platforms, False)
        
        for platform in hit_list_y:
            if current_gravity == "DOWN":
                if self.vel_y > 0: # 下に落ちている時 (着地)
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                elif self.vel_y < 0: # 頭をぶつけた時
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0 
            
            elif current_gravity == "UP":
                if self.vel_y < 0: # "下" (天井方向) に落ちている時 (着地)
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
                elif self.vel_y > 0: # "頭" (床方向) をぶつけた時
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0

        # --- 6. 接地判定 ---
        self.on_ground = False
        self.standing_on.clear() 
        
        check_rect = self.rect.copy()
        if current_gravity == "DOWN":
            check_rect.y += 1
        elif current_gravity == "UP":
            check_rect.y -= 1
        
        # spritecollide は使えないため、手動でループ処理する
        ground_hit_list = []
        for platform in platforms:
            if check_rect.colliderect(platform.rect):
                ground_hit_list.append(platform)

        if len(ground_hit_list) > 0:
            self.on_ground = True
            self.standing_on = ground_hit_list
    
    def jump(self, current_gravity):
        # キー入力をこのメソッド内で取得
        keys = pygame.key.get_pressed()

        # 1. 地上ジャンプの判定
        if self.on_ground:
            power = self.jump_multiplier
            if current_gravity == "DOWN":
                self.vel_y = JUMP_STRENGTH * power
            elif current_gravity == "UP":
                self.vel_y = -JUMP_STRENGTH * power

        # 2. 壁キックの判定 (空中で、壁に触れている)
        elif self.on_wall != 0:
            
            # 壁側にキー入力しているかチェック
            is_pushing_into_wall = False
            
            # 左壁 (self.on_wall == -1) に触れていて、左キーを押している
            if self.on_wall == -1 and (keys[pygame.K_LEFT] or keys[pygame.K_a]):
                 is_pushing_into_wall = True
            
            # 右壁 (self.on_wall == 1) に触れていて、右キーを押している
            elif self.on_wall == 1 and (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                 is_pushing_into_wall = True

            # 壁に入力している時だけ、壁キックを実行
            if is_pushing_into_wall:
                # 重力方向に応じて、キックの向きを変える
                if current_gravity == "DOWN":
                    self.vel_y = WALL_JUMP_STRENGTH_Y # 上向き (-19)
                else: # current_gravity == "UP"
                    self.vel_y = -WALL_JUMP_STRENGTH_Y # 下向き (19)
                # (壁キックは現在の重力方向に関わらず、常に上方向へ飛ぶ)
                self.vel_x = -self.on_wall * WALL_JUMP_STRENGTH_X
                self.wall_jump_cooldown = self.WALL_JUMP_COOLDOWN_FRAMES
                self.on_wall = 0
            
    def cut_jump(self):
        # (下向き重力でジャンプ中 = 上昇中)
        if self.vel_y < 0: 
            self.vel_y *= 0.4 
        # (メモ: 上向き重力時 (vel_y > 0) のcut_jumpも必要なら追加)

    def reset_position(self, x, y):
        self.rect.topleft = (x, y)
        self.vel_x = 0 
        self.vel_y = 0
        self.on_ground = False
        self.has_key = False
        self.speed_multiplier = 1.0
        self.jump_multiplier = 1.0
        self.standing_on.clear() 
        self.wall_jump_cooldown = 0 # クールダウンもリセット

# --- その他のオブジェクトクラス ---
class Platform(pygame.sprite.Sprite):
    """足場 (シームレスな線画対応)"""
    def __init__(self, x, y, up, down, left, right):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0)) 
        
        if not up:
            pygame.draw.line(self.image, PLATFORM_BORDER_COLOR, (0, 0), (TILE_SIZE - 1, 0), 1)
        if not down:
            pygame.draw.line(self.image, PLATFORM_BORDER_COLOR, (0, TILE_SIZE - 1), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
        if not left:
            pygame.draw.line(self.image, PLATFORM_BORDER_COLOR, (0, 0), (0, TILE_SIZE - 1), 1)
        if not right:
            pygame.draw.line(self.image, PLATFORM_BORDER_COLOR, (TILE_SIZE - 1, 0), (TILE_SIZE - 1, TILE_SIZE - 1), 1)

        self.rect = self.image.get_rect(topleft=(x, y))

class BoosterPlatform(Platform):
    def __init__(self, x, y, up, down, left, right):
        super().__init__(x, y, up, down, left, right)
        self.image.fill(BOOSTER_COLOR) # 見やすいように塗りつぶし

class GravitySwitcher(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((25, 25))
        self.image.fill(GRAVITY_SWITCHER_COLOR)
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))

class Spike(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE // 2), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0)) 

        points = [
            (0, TILE_SIZE // 2),
            (TILE_SIZE // 2, 0),
            (TILE_SIZE, TILE_SIZE // 2)
        ]
        pygame.draw.polygon(self.image, SPIKE_COLOR, points)
        self.rect = self.image.get_rect(topleft=(x, y + TILE_SIZE // 2))

class Key(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(KEY_COLOR)
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))

class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill(DOOR_COLOR)
        self.rect = self.image.get_rect(bottomleft=(x, y + TILE_SIZE))

# --- ステージを構築する関数 ---
def setup_level(level_map):
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    spikes = pygame.sprite.Group()
    keys = pygame.sprite.Group()
    doors = pygame.sprite.Group()
    booster_platforms = pygame.sprite.Group()
    gravity_switchers = pygame.sprite.Group()
    
    player = None
    start_pos = (0, 0)
    
    map_height = len(level_map)
    map_width = len(level_map[0])
    
    for y, row in enumerate(level_map):
        for x, char in enumerate(row):
            world_x = x * TILE_SIZE
            world_y = y * TILE_SIZE
            
            has_neighbor_up = (y > 0 and level_map[y - 1][x] in ('P', 'B'))
            has_neighbor_down = (y < map_height - 1 and level_map[y + 1][x] in ('P', 'B'))
            has_neighbor_left = (x > 0 and level_map[y][x - 1] in ('P', 'B'))
            has_neighbor_right = (x < map_width - 1 and level_map[y][x + 1] in ('P', 'B'))

            if char == 'P':
                p = Platform(world_x, world_y, 
                             has_neighbor_up, has_neighbor_down, 
                             has_neighbor_left, has_neighbor_right)
                platforms.add(p)
                all_sprites.add(p)
            
            elif char == 'B': # Booster
                b = BoosterPlatform(world_x, world_y,
                                    has_neighbor_up, has_neighbor_down,
                                    has_neighbor_left, has_neighbor_right)
                platforms.add(b) 
                booster_platforms.add(b)
                all_sprites.add(b)
            elif char == 'G': # GravitySwitcher
                g = GravitySwitcher(world_x, world_y)
                gravity_switchers.add(g)
                all_sprites.add(g)

            elif char == 'S': # Spike
                s = Spike(world_x, world_y)
                spikes.add(s)
                all_sprites.add(s)
            elif char == 'K': # Key
                k = Key(world_x, world_y)
                keys.add(k)
                all_sprites.add(k)
            elif char == 'D': # Door
                d = Door(world_x, world_y)
                doors.add(d)
                all_sprites.add(d)
            elif char == '@': # Player
                player_x = world_x + (TILE_SIZE - 30) // 2
                player_y = world_y + (TILE_SIZE - 30)
                start_pos = (player_x, player_y)
                player = Player(player_x, player_y)

    if player is None:
        print("エラー: プレイヤー(@)がマップにいません！")
        sys.exit()

    all_sprites.add(player)
    
    return player, start_pos, all_sprites, platforms, spikes, keys, doors, gravity_switchers, booster_platforms

class Arrow(pygame.sprite.Sprite):
    """★ 弓矢（飛んでくる障害物）"""
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((30, 8))
        self.image.fill(ARROW_COLOR) 
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.direction = direction # -1: 左向き, 1: 右向き
        self.speed = 8 

    def update(self):
        self.rect.x += self.speed * self.direction
        
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill() 

class ArrowLauncher(pygame.sprite.Sprite):
    """★ 弓矢の発射台 (固定オブジェクトとして描画)"""
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((20, 20)) # 発射台のサイズ
        self.image.fill(LAUNCHER_COLOR)
        
        if direction == -1: # 左向きに発射 (右側の壁)
             # x座標は画面の端 (SCREEN_WIDTH) を指定し、toprightで配置
             self.rect = self.image.get_rect(topright=(x, y)) 
        else: # 右向きに発射 (左側の壁)
             # x座標は 0 を指定し、topleftで配置
             self.rect = self.image.get_rect(topleft=(x, y))
             
        self.direction = direction # 弓矢の進行方向

class FallingSpike(Spike):
    """プレイヤーが近づくと落ちてくるトゲ"""
    def __init__(self, x, y, w, h):
        # 元のSpikeクラスの機能をもらう
        super().__init__(x, y, w, h)
        
        self.vel_y = 0
        self.is_active = False # 起動したかどうか
        self.start_y = y       # スタート位置のY座標を覚えておく

    def update(self, platforms):
        # 起動(is_active)してたら、重力で落ちる
        if self.is_active:
            self.vel_y += GRAVITY
            if self.vel_y > 10: # 最大落下速度
                self.vel_y = 10
            
            self.rect.y += self.vel_y

            # 地面(platforms)に着地したら止まる
            hit_list = pygame.sprite.spritecollide(self, platforms, False)
            for platform in hit_list:
                if self.vel_y > 0: # 下に落ちてる時
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    # (地面に着いたら、もう動かなくていい)
                    self.is_active = False 

    def activate(self):
        """トゲを起動させる（落ち始める）"""
        if not self.is_active and self.vel_y == 0:
            self.is_active = True
            # print("トゲ起動！") # デバッグ用

    def reset_position(self):
        """トゲを元の位置に戻す"""
        self.rect.y = self.start_y
        self.vel_y = 0
        self.is_active = False

class PatrollingSpike(Spike):
    """指定された範囲を左右に往復するトゲ"""
    def __init__(self, x, y, w, h, move_range, speed):
        # 元のSpikeクラスの機能をもらう
        super().__init__(x, y, w, h)
        
        self.start_x = x             # スタートのX座標
        self.end_x = x + move_range  # ここまで動く（右に move_range ピクセル）
        self.vel_x = speed           # 動く速さ
        
        self.original_x = x          # リセット用の初期位置X
        self.original_y = y          # リセット用の初期位置Y
        self.original_speed = speed  # リセット用の初期速度

    def update(self):
        # 左右に移動
        self.rect.x += self.vel_x
        
        # 範囲の端に来たら反転
        if self.rect.x > self.end_x:
            self.rect.x = self.end_x # はみ出ないように
            self.vel_x = -self.vel_x # 反対方向へ
        elif self.rect.x < self.start_x:
            self.rect.x = self.start_x # はみ出ないように
            self.vel_x = -self.vel_x # 反対方向へ

    def reset_position(self):
        """トゲを元の位置に戻す"""
        self.rect.topleft = (self.original_x, self.original_y)
        self.vel_x = self.original_speed


class Arrow(pygame.sprite.Sprite):
    """★ 弓矢（飛んでくる障害物）"""
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((30, 8))
        self.image.fill(ARROW_COLOR) 
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.direction = direction # -1: 左向き, 1: 右向き
        self.speed = 8 

    def update(self):
        self.rect.x += self.speed * self.direction
        
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill() 

class ArrowLauncher(pygame.sprite.Sprite):
    """★ 弓矢の発射台 (固定オブジェクトとして描画)"""
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((20, 20)) # 発射台のサイズ
        self.image.fill(LAUNCHER_COLOR)
        
        if direction == -1: # 左向きに発射 (右側の壁)
             # x座標は画面の端 (SCREEN_WIDTH) を指定し、toprightで配置
             self.rect = self.image.get_rect(topright=(x, y)) 
        else: # 右向きに発射 (左側の壁)
             # x座標は 0 を指定し、topleftで配置
             self.rect = self.image.get_rect(topleft=(x, y))
             
        self.direction = direction # 弓矢の進行方向

class FallingSpike(Spike):
    """プレイヤーが近づくと落ちてくるトゲ"""
    def __init__(self, x, y, w, h):
        # 元のSpikeクラスの機能をもらう
        super().__init__(x, y, w, h)
        
        self.vel_y = 0
        self.is_active = False # 起動したかどうか
        self.start_y = y       # スタート位置のY座標を覚えておく

    def update(self, platforms):
        # 起動(is_active)してたら、重力で落ちる
        if self.is_active:
            self.vel_y += GRAVITY
            if self.vel_y > 10: # 最大落下速度
                self.vel_y = 10
            
            self.rect.y += self.vel_y

            # 地面(platforms)に着地したら止まる
            hit_list = pygame.sprite.spritecollide(self, platforms, False)
            for platform in hit_list:
                if self.vel_y > 0: # 下に落ちてる時
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    # (地面に着いたら、もう動かなくていい)
                    self.is_active = False 

    def activate(self):
        """トゲを起動させる（落ち始める）"""
        if not self.is_active and self.vel_y == 0:
            self.is_active = True
            # print("トゲ起動！") # デバッグ用

    def reset_position(self):
        """トゲを元の位置に戻す"""
        self.rect.y = self.start_y
        self.vel_y = 0
        self.is_active = False

class PatrollingSpike(Spike):
    """指定された範囲を左右に往復するトゲ"""
    def __init__(self, x, y, w, h, move_range, speed):
        # 元のSpikeクラスの機能をもらう
        super().__init__(x, y, w, h)
        
        self.start_x = x             # スタートのX座標
        self.end_x = x + move_range  # ここまで動く（右に move_range ピクセル）
        self.vel_x = speed           # 動く速さ
        
        self.original_x = x          # リセット用の初期位置X
        self.original_y = y          # リセット用の初期位置Y
        self.original_speed = speed  # リセット用の初期速度

    def update(self):
        # 左右に移動
        self.rect.x += self.vel_x
        
        # 範囲の端に来たら反転
        if self.rect.x > self.end_x:
            self.rect.x = self.end_x # はみ出ないように
            self.vel_x = -self.vel_x # 反対方向へ
        elif self.rect.x < self.start_x:
            self.rect.x = self.start_x # はみ出ないように
            self.vel_x = -self.vel_x # 反対方向へ

    def reset_position(self):
        """トゲを元の位置に戻す"""
        self.rect.topleft = (self.original_x, self.original_y)
        self.vel_x = self.original_speed


# --- メインゲーム処理 ---
# --- メインゲーム処理 ---
def main():
    gravity_direction = "DOWN"
    
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    
    pygame.display.set_caption("Gravity Switch Prototype (Optimized)")
    clock = pygame.time.Clock()

    # --- レベルのセットアップ ---
    # all_sprites = pygame.sprite.Group() 
    # ( ... 古いセットアップコード (663行目〜734行目) をすべて削除 ... )
    # floor = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40) # <--- エラーの発生源 (削除)
    # ( ... )
    # next_arrow_launch_time = current_time + random.randint(MIN_ARROW_INTERVAL, MAX_ARROW_INTERVAL) # <--- (削除)


    while True:
        player, start_pos, all_sprites, platforms, spikes, keys, doors, gravity_switchers, booster_platforms = setup_level(LEVEL_MAP)
        
        level_width = len(LEVEL_MAP[0]) * TILE_SIZE
        level_height = len(LEVEL_MAP) * TILE_SIZE
        
        camera_x = 0
        camera_y = 0
        
        game_state = "PLAYING"
        animation_timer = 0.0
        animation_duration = 120.0 # (2秒)
        current_screen_angle = 0.0
        current_scale = 1.0
        start_angle = 0.0
        target_angle = 0.0
        target_gravity = "DOWN"

        while True:
            # --- イベント処理 ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if game_state == "PLAYING":
                    if event.type == pygame.KEYDOWN:
                        
                        if event.key == pygame.K_SPACE:
                            player.jump(gravity_direction) 
                        
                        elif gravity_direction == "DOWN":
                            if event.key == pygame.K_UP or event.key == pygame.K_w:
                                player.jump(gravity_direction) 
                        elif gravity_direction == "UP":
                                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                                    player.jump(gravity_direction) 
                        
                    if event.type == pygame.KEYUP:
                        if gravity_direction == "DOWN":
                            if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                                player.cut_jump()

            # --- 更新処理 ---
            if game_state == "PLAYING":
                player.update(platforms, gravity_direction) 

                # 落下ミス判定
                if (player.rect.top > level_height or player.rect.bottom < 0 or
                    player.rect.left > level_width or player.rect.right < 0):
                    
                    print("落下ミス！リスタートします。")
                    all_sprites.empty(); platforms.empty(); spikes.empty(); keys.empty()
                    doors.empty(); gravity_switchers.empty(); booster_platforms.empty()
                    player, start_pos, all_sprites, platforms, spikes, keys, doors, gravity_switchers, booster_platforms = setup_level(LEVEL_MAP)
                    
                    player.reset_position(*start_pos)
                    gravity_direction = "DOWN"
                    current_screen_angle = 0.0 
                    
                # ブースター判定
                is_on_booster = any(isinstance(p, BoosterPlatform) for p in player.standing_on) if player.on_ground else False
                player.speed_multiplier = 2.0 if is_on_booster else 1.0
                # ジャンプ力
                player.jump_multiplier = 10.0 if is_on_booster else 1.0

                # 重力スイッチ判定
                collided_switcher = pygame.sprite.spritecollideany(player, gravity_switchers)
                if collided_switcher:
                    
                    target_gravity = "UP" if gravity_direction == "DOWN" else "DOWN"
                    print(f"スイッチ接触！ 次の重力: {target_gravity}") 

                    game_state = "ANIMATING"
                    animation_timer = 0.0
                    start_angle = current_screen_angle 
                    target_angle = get_angle_from_gravity(target_gravity)
                    
                    diff = target_angle - start_angle
                    if diff > 180: target_angle -= 360
                    elif diff < -180: target_angle += 360
                    
                    collided_switcher.kill() 
                    print(f"重力変更開始: {gravity_direction} -> {target_gravity}")
                
                # カメラの更新
                target_camera_x = player.rect.centerx - (GAME_WIDTH // 3) 
                target_camera_x = max(0, min(target_camera_x, level_width - GAME_WIDTH))
                camera_x += (target_camera_x - camera_x) / 20.0 
                
                target_camera_y = player.rect.centery - (GAME_HEIGHT // 2)
                target_camera_y = max(0, min(target_camera_y, level_height - GAME_HEIGHT))
                camera_y += (target_camera_y - camera_y) / 20.0 
                
                # トゲとの衝突判定
                if pygame.sprite.spritecollide(player, spikes, False):
                    print("ミス！リスタートします。")
                    all_sprites.empty(); platforms.empty(); spikes.empty(); keys.empty()
                    doors.empty(); gravity_switchers.empty(); booster_platforms.empty()
                    player, start_pos, all_sprites, platforms, spikes, keys, doors, gravity_switchers, booster_platforms = setup_level(LEVEL_MAP)
                    
                    player.reset_position(*start_pos)
                    gravity_direction = "DOWN"
                    current_screen_angle = 0.0

                # --- 更新処理 ---
                # ( ... 弓矢や古いトゲのロジック (844行目〜917行目) を削除 ... )
                # current_time = pygame.time.get_ticks() # <--- (削除)
                # if current_time > next_arrow_launch_time: # <--- (削除)
                # player.update(platforms) # <--- (削除 - 重複)
                # arrows.update() # <--- (削除)
                # ...
                # if pygame.sprite.spritecollide(player, arrows, True): # <--- (削除)


                # カギ・トビラ判定
                # <--- (注: 'if game_state == "PLAYING":' のブロック内に正しくインデント)
                if pygame.sprite.spritecollide(player, keys, True):
                    player.has_key = True
                    print("カギを手に入れた！")
                
                if pygame.sprite.spritecollideany(player, doors) and player.has_key:
                    print("クリア！おめでとう！")
                    pygame.quit()
                    sys.exit()

                current_scale = 1.0

            elif game_state == "ANIMATING":
                # アニメーション中の更新処理
                animation_timer += 1
                progress = min(animation_timer / animation_duration, 1.0)
                ease_progress = 1 - pow(1 - progress, 3) 

                current_scale = 1.0 - 0.8 * math.sin(ease_progress * math.pi) 
                current_screen_angle = start_angle + (target_angle - start_angle) * ease_progress
                
                if progress >= 1.0:
                    game_state = "PLAYING"
                    gravity_direction = target_gravity
                    current_screen_angle = get_angle_from_gravity(target_gravity)
                    print(f"重力が {gravity_direction} に変更完了！")

            
            # --- 描画処理 (ズーム・回転アニメーション対応) ---
            
            # 1. 仮想スクリーン (game_surface) にゲーム内容を描画
            game_surface.fill(BLACK) 
            for sprite in all_sprites:
                screen_x = sprite.rect.x - camera_x
                screen_y = sprite.rect.y - camera_y
                game_surface.blit(sprite.image, (screen_x, screen_y)) 
            
            # 2. game_surface を screen サイズに引き伸ばした「基本表示画面」を作成
            base_display_surface = pygame.transform.scale(game_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
            # 3. 実際のウィンドウ (screen) を白で塗りつぶす (アニメーション背景用)
            screen.fill(WHITE)

            # 4. アニメーション変数に基づいて「基本表示画面」を変形
            scaled_width = int(SCREEN_WIDTH * current_scale)
            scaled_height = int(SCREEN_HEIGHT * current_scale)
            scaled_surface = pygame.transform.scale(base_display_surface, (scaled_width, scaled_height))
            
            rotated_surface = pygame.transform.rotate(scaled_surface, current_screen_angle)
            
            # 5. 変形させたサーフェスを「画面の中央」に描画
            center_x = SCREEN_WIDTH // 2
            center_y = SCREEN_HEIGHT // 2
            draw_rect = rotated_surface.get_rect(center=(center_x, center_y)) 
            
            screen.blit(rotated_surface, draw_rect)

            # 6. 実際の画面を更新
            pygame.display.flip()
            clock.tick(FPS)

if __name__ == "__main__":
    main()