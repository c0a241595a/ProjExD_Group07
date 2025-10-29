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

# ゲームの「見える範囲」 (カメラのズーム設定)
GAME_WIDTH = 640
GAME_HEIGHT = 480

FPS = 60
TILE_SIZE = 40 # 1マスのサイズ

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COLOR = (50, 50, 255)    # プレイヤー (青)
PLATFORM_COLOR = (100, 100, 100) # 足場 (灰色)
SPIKE_COLOR = (255, 50, 50)    # 障害物 (赤)
KEY_COLOR = (255, 215, 0) # カギ (黄)
DOOR_COLOR = (0, 200, 0)      # トビラ (緑)
PLAYER_BORDER_COLOR = (255, 255, 255) # プレイヤーの枠の色 (白)
PLATFORM_BORDER_COLOR = (255, 255, 255) # 足場の枠の色 (白)
BOOSTER_COLOR = (50, 255, 50) # ブースターの色 (明るい緑)
GRAVITY_SWITCHER_COLOR = (200, 50, 200) # 重力スイッチの色 (紫)


# 物理定数
GRAVITY = 0.8
JUMP_STRENGTH = -15 # JUMP_POWER ではなく JUMP_STRENGTH に統一
MOVE_SPEED = 5      # PLAYER_SPEED を MOVE_SPEED に変更
MAX_SPEED = 6           # プレイヤーの最高速度
ACCELERATION = 0.4        # 加速の度合い
FRICTION_FORCE = 0.2        # 摩擦力

# ヘルパー関数
def get_angle_from_gravity(direction):
    if direction == "DOWN":
        return 0
    elif direction == "LEFT":
        return 90
    elif direction == "UP":
        return 180
    elif direction == "RIGHT":
        return 270
    return 0


# --- ステージの設計図 (重力スイッチ 'G' を追加) ---
LEVEL_MAP = [
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", # Y=0
    "P......................................P",
    "P....@...PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", # Y=2 (スタート)
    "P....P.................................P",
    "PPPPPP...PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", # Y=4
    "P........P.............................P",
    "P..SSSS..P...PPPPPPPPPPPPPPPPPPPPPPPPPPP",
    "P..PPPPP.P...P.........................P",
    "P........P...P...S.S...................P",
    "PPPPPPPPPP...P..PPPPP...PPPPPPPPPPPPPPPP",
    "P............P..........P..............P",
    "P....K.......P..........P..............P", # Y=11 (カギ)
    "PPPPPPPPPPPPPP..........P...PPPPPPPPPPPP",
    "P...............G.......P...P..........P", # ▼修正: Y=13 に 'G' を追加
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


# --- プレイヤークラス (修正版) ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0)) # 完全に透過
        # 白い枠線で、角の丸い四角を描画
        pygame.draw.rect(self.image, PLAYER_BORDER_COLOR, self.image.get_rect(), 
                         width=1, border_radius=4)
        
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.has_key = False
        
        self.speed_multiplier = 1.0
        self.jump_multiplier = 1.0
        self.standing_on = [] 

    def update(self, platforms, current_gravity):
        """
        物理演算と衝突判定、on_ground判定を修正
        """
        keys = pygame.key.get_pressed()
        
        # --- 1. 入力処理 (重力基準の移動) ---
        target_vel_x = 0
        target_vel_y = 0

        # 重力が上下の場合、左右キーがX軸移動
        if current_gravity in ["DOWN", "UP"]:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                target_vel_x = -MOVE_SPEED * self.speed_multiplier
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                target_vel_x = MOVE_SPEED * self.speed_multiplier
        
        # 重力が左右の場合、上下キーがY軸移動
        if current_gravity in ["LEFT", "RIGHT"]:
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                target_vel_y = -MOVE_SPEED * self.speed_multiplier
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                target_vel_y = MOVE_SPEED * self.speed_multiplier
                
        
        # --- 2. 物理演算 (加速/摩擦/重力) ---

        # X軸の加速と摩擦 (重力が上下の時のみ)
        if current_gravity in ["DOWN", "UP"]:
            if target_vel_x != 0: # 加速
                self.vel_x += (target_vel_x - self.vel_x) * ACCELERATION
            else: # 摩擦
                self.vel_x *= (1.0 - FRICTION_FORCE)
            
            if abs(self.vel_x) < 0.1: self.vel_x = 0
            self.vel_x = max(-MAX_SPEED, min(self.vel_x, MAX_SPEED))
            
            # 重力
            if not self.on_ground:
                if current_gravity == "DOWN":
                    self.vel_y += GRAVITY
                elif current_gravity == "UP":
                    self.vel_y -= GRAVITY
                self.vel_y = max(-10, min(self.vel_y, 10))

        # Y軸の加速と摩擦 (重力が左右の時のみ)
        if current_gravity in ["LEFT", "RIGHT"]:
            if target_vel_y != 0: # 加速
                self.vel_y += (target_vel_y - self.vel_y) * ACCELERATION
            else: # 摩擦
                self.vel_y *= (1.0 - FRICTION_FORCE)

            if abs(self.vel_y) < 0.1: self.vel_y = 0
            self.vel_y = max(-MAX_SPEED, min(self.vel_y, MAX_SPEED))

            # 重力
            if not self.on_ground:
                if current_gravity == "LEFT":
                    self.vel_x -= GRAVITY
                elif current_gravity == "RIGHT":
                    self.vel_x += GRAVITY
                self.vel_x = max(-10, min(self.vel_x, 10))


        # --- 3. 衝突判定 (X軸) ---
        self.rect.x += self.vel_x
        hit_list_x = pygame.sprite.spritecollide(self, platforms, False)
        for platform in hit_list_x:
            if self.vel_x > 0: # 右に移動中
                self.rect.right = platform.rect.left
            elif self.vel_x < 0: # 左に移動中
                self.rect.left = platform.rect.right
            self.vel_x = 0 

        # --- 4. Y軸の移動と衝突判定 ---
        self.rect.y += self.vel_y
        hit_list_y = pygame.sprite.spritecollide(self, platforms, False)
        for platform in hit_list_y:
            if self.vel_y > 0: # 下に移動中
                self.rect.bottom = platform.rect.top
            elif self.vel_y < 0: # 上に移動中
                self.rect.top = platform.rect.bottom
            self.vel_y = 0 

        # --- 5. 接地判定 (重力方向基準) ---
        # ▼▼▼【ジャンプできない問題の修正箇所】▼▼▼
        self.on_ground = False
        self.standing_on.clear() 
        
        # (1) 元のrectを保存
        original_rect = self.rect.copy() 
        
        # (2) 重力方向にrectを1ピクセルずらす
        if current_gravity == "DOWN":
            self.rect.y += 1
        elif current_gravity == "UP":
            self.rect.y -= 1
        elif current_gravity == "LEFT":
            self.rect.x -= 1
        elif current_gravity == "RIGHT":
            self.rect.x += 1
            
        # (3) 1ピクセルずらした状態で、platformsと衝突しているか判定
        ground_hit_list = pygame.sprite.spritecollide(self, platforms, False)

        if ground_hit_list:
            self.on_ground = True
            self.standing_on = ground_hit_list
            
        # (4) rectを必ず元の位置に戻す
        self.rect = original_rect 
        # ▲▲▲【修正ここまで】▲▲▲

    def jump(self, current_gravity):
        # 地面にいる時だけジャンプできる
        if self.on_ground:
            power = self.jump_multiplier
            
            if current_gravity == "DOWN":
                self.vel_y = JUMP_STRENGTH * power
            elif current_gravity == "UP":
                self.vel_y = -JUMP_STRENGTH * power
            elif current_gravity == "LEFT":
                self.vel_x = -JUMP_STRENGTH * power
            elif current_gravity == "RIGHT":
                self.vel_x = JUMP_STRENGTH * power

    def cut_jump(self):
        # ジャンプキーを離した時に呼ばれる (下向き重力専用)
        if self.vel_y < 0:
            self.vel_y *= 0.4 

    def reset_position(self, x, y):
        self.rect.topleft = (x, y)
        self.vel_x = 0 
        self.vel_y = 0
        self.on_ground = False
        self.has_key = False
        self.speed_multiplier = 1.0
        self.jump_multiplier = 1.0
        self.standing_on.clear() 

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
        self.image.fill(BOOSTER_COLOR) 

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

# --- メインゲーム処理 (カメラ・ズーム対応) ---
def main():
    gravity_direction = "DOWN"
    
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    
    pygame.display.set_caption("Gravity Switch Prototype (Expanded)")
    clock = pygame.time.Clock()

    # --- レベルのセットアップ ---
    player, start_pos, all_sprites, platforms, spikes, keys, doors, gravity_switchers, booster_platforms = setup_level(LEVEL_MAP)
    
    level_width = len(LEVEL_MAP[0]) * TILE_SIZE
    level_height = len(LEVEL_MAP) * TILE_SIZE
    
    camera_x = 0
    camera_y = 0
    
    # --- アニメーション用変数 ---
    game_state = "PLAYING"
    animation_timer = 0.0
    animation_duration = 60.0 
    current_screen_angle = 0.0
    current_scale = 1.0
    start_angle = 0.0
    target_angle = 0.0
    target_gravity = "DOWN"
    # temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)) # (回転アニメーション用、現在未使用)


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

                    elif gravity_direction == "LEFT":
                            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                                player.jump(gravity_direction) 
                    elif gravity_direction == "RIGHT":
                            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                                player.jump(gravity_direction) 
                
                if event.type == pygame.KEYUP:
                    if gravity_direction == "DOWN":
                        if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                            player.cut_jump() 


        # --- 状態分岐による「更新」処理 ---
        if game_state == "PLAYING":
            player.update(platforms, gravity_direction) 

            # 落下ミス判定
            if (player.rect.top > level_height or player.rect.bottom < 0 or
                player.rect.left > level_width or player.rect.right < 0):
                
                print("落下ミス！リスタートします。")
                player.reset_position(*start_pos)
                gravity_direction = "DOWN"
                current_screen_angle = 0.0 
                player.has_key = False 
                
                # ▼修正: アイテムとスイッチを復活させる (暫定的なリロード)
                # (本来は各グループを setup_level に渡してクリア・再追加するのが望ましい)
                all_sprites.empty()
                platforms.empty()
                spikes.empty()
                keys.empty()
                doors.empty()
                gravity_switchers.empty()
                booster_platforms.empty()
                
                player, start_pos, all_sprites, platforms, spikes, keys, doors, gravity_switchers, booster_platforms = setup_level(LEVEL_MAP)


            # ブースター判定
            is_on_booster = False
            if player.on_ground:
                for platform in player.standing_on:
                    if isinstance(platform, BoosterPlatform):
                        is_on_booster = True
                        break
            
            player.speed_multiplier = 2.0 if is_on_booster else 1.0
            player.jump_multiplier = 2.0 if is_on_booster else 1.0

            # 重力スイッチ判定
            collided_switcher = pygame.sprite.spritecollideany(player, gravity_switchers)
            if collided_switcher:
                directions = ["UP", "DOWN", "LEFT", "RIGHT"]
                if gravity_direction in directions:
                    directions.remove(gravity_direction)
                target_gravity = random.choice(directions)
                
                print(f"スイッチ接触！ 次の重力: {target_gravity}") 

                game_state = "ANIMATING"
                animation_timer = 0.0
                start_angle = current_screen_angle 
                target_angle = get_angle_from_gravity(target_gravity)
                
                diff = target_angle - start_angle
                if diff > 180:
                    target_angle -= 360
                elif diff < -180:
                    target_angle += 360
                
                collided_switcher.kill() 
                print(f"重力変更開始: {gravity_direction} -> {target_gravity}")
            
            # --- カメラの更新 ---
            target_camera_x = player.rect.centerx - (GAME_WIDTH // 3) 
            target_camera_x = max(0, min(target_camera_x, level_width - GAME_WIDTH))
            camera_x += (target_camera_x - camera_x) / 20.0 
            
            target_camera_y = player.rect.centery - (GAME_HEIGHT // 2)
            target_camera_y = max(0, min(target_camera_y, level_height - GAME_HEIGHT))
            camera_y += (target_camera_y - camera_y) / 20.0 
            

            # トゲとの衝突判定
            if pygame.sprite.spritecollide(player, spikes, False):
                print("ミス！リスタートします。")
                player.reset_position(*start_pos)
                gravity_direction = "DOWN"
                current_screen_angle = 0.0
                player.has_key = False
                
                # ▼修正: アイテムとスイッチを復活させる (暫定的なリロード)
                all_sprites.empty()
                platforms.empty()
                spikes.empty()
                keys.empty()
                doors.empty()
                gravity_switchers.empty()
                booster_platforms.empty()
                
                player, start_pos, all_sprites, platforms, spikes, keys, doors, gravity_switchers, booster_platforms = setup_level(LEVEL_MAP)


            # カギ・トビラ判定
            collided_keys = pygame.sprite.spritecollide(player, keys, True)
            if collided_keys:
                player.has_key = True
                print("カギを手に入れた！")
            
            if pygame.sprite.spritecollideany(player, doors) and player.has_key:
                print("クリア！おめでとう！")
                pygame.quit()
                sys.exit()

            current_scale = 1.0

        elif game_state == "ANIMATING":
            # --- アニメーション中の更新処理 ---
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


        # --- 描画処理 (ズーム対応) ---
        
        # 1. 小さい仮想スクリーン (game_surface) を黒で塗りつぶす
        game_surface.fill(BLACK) 
        
        # 2. 仮想スクリーンに、カメラ座標を引いて全スプライトを描画
        for sprite in all_sprites:
            screen_x = sprite.rect.x - camera_x
            screen_y = sprite.rect.y - camera_y
            game_surface.blit(sprite.image, (screen_x, screen_y)) 
        
        # 3. 仮想スクリーンを、実際の画面サイズに引き伸ばして表示
        # (回転・拡縮アニメーションは現在無効)
        scaled_surface = pygame.transform.scale(game_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        
        # 4. 実際の画面を更新
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()