import pygame
import sys
import os
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
SPIKE_COLOR = (255, 50, 50)   # 障害物 (赤)
KEY_COLOR = (255, 215, 0) # カギ (黄)
DOOR_COLOR = (0, 200, 0)    # トビラ (緑)

PLAYER_BORDER_COLOR = (255, 255, 255) # プレイヤーの枠の色 (白)
PLATFORM_BORDER_COLOR = (255, 255, 255) # 足場の枠の色 (白)

# 物理定数 (慣性・摩擦あり)
GRAVITY = 0.7             # 重力
JUMP_STRENGTH = -16       # ジャンプ力
MAX_SPEED = 6             # プレイヤーの最高速度
ACCELERATION = 0.4        # 加速の度合い
FRICTION_FORCE = 0.2      # 摩擦力

# --- ステージの設計図 (ほぼ一本道・障害物増量) ---
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


# --- プレイヤークラス (慣性・角丸・可変ジャンプ対応) ---
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

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        
        # --- 1. X軸の物理演算 (加速と摩擦) ---
        moving_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        moving_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        # A. 加速
        if moving_left and not moving_right:
            self.vel_x -= ACCELERATION
        elif moving_right and not moving_left:
            self.vel_x += ACCELERATION
        # B. 摩擦
        else:
            if self.vel_x > 0:
                self.vel_x -= FRICTION_FORCE
                if self.vel_x < 0: self.vel_x = 0 
            elif self.vel_x < 0:
                self.vel_x += FRICTION_FORCE
                if self.vel_x > 0: self.vel_x = 0 

        # C. 最高速度制限
        if self.vel_x > MAX_SPEED:
            self.vel_x = MAX_SPEED
        elif self.vel_x < -MAX_SPEED:
            self.vel_x = -MAX_SPEED

        # --- 2. Y軸の物理演算 (重力) ---
        if not self.on_ground:
            self.vel_y += GRAVITY
            if self.vel_y > 10: # 最大落下速度
                self.vel_y = 10

        # --- 3. 衝突判定 (X軸) ---
        self.rect.x += self.vel_x
        hit_list_x = pygame.sprite.spritecollide(self, platforms, False)
        for platform in hit_list_x:
            if self.vel_x > 0: 
                self.rect.right = platform.rect.left
            elif self.vel_x < 0: 
                self.rect.left = platform.rect.right
            self.vel_x = 0 # 壁にぶつかったら横速度をリセット

        # --- 4. 衝突判定 (Y軸) ---
        self.rect.y += self.vel_y
        hit_list_y = pygame.sprite.spritecollide(self, platforms, False)
        for platform in hit_list_y:
            if self.vel_y > 0: 
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
            elif self.vel_y < 0: 
                self.rect.top = platform.rect.bottom
                self.vel_y = 0

        # --- 5. 接地判定 ---
        self.rect.y += 1
        ground_hit_list = pygame.sprite.spritecollide(self, platforms, False)
        self.rect.y -= 1 
        self.on_ground = len(ground_hit_list) > 0

    def jump(self):
        # 地面にいる時だけジャンプできる
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH

    def cut_jump(self):
        # ジャンプキーを離した時に呼ばれる
        if self.vel_y < 0:
            self.vel_y *= 0.4 # 上昇力をカット

    def reset_position(self, x, y):
        self.rect.topleft = (x, y)
        self.vel_x = 0 # 速度もリセット
        self.vel_y = 0
        self.on_ground = False
        self.has_key = False

# --- その他のオブジェクトクラス ---
class Platform(pygame.sprite.Sprite):
    """足場 (シームレスな線画対応)"""
    def __init__(self, x, y, up, down, left, right):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0)) # 完全に透過
        
        # 隣に 'P' が「ない」辺だけ線を描画する
        if not up:
            pygame.draw.line(self.image, PLATFORM_BORDER_COLOR, (0, 0), (TILE_SIZE - 1, 0), 1)
        if not down:
            pygame.draw.line(self.image, PLATFORM_BORDER_COLOR, (0, TILE_SIZE - 1), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
        if not left:
            pygame.draw.line(self.image, PLATFORM_BORDER_COLOR, (0, 0), (0, TILE_SIZE - 1), 1)
        if not right:
            pygame.draw.line(self.image, PLATFORM_BORDER_COLOR, (TILE_SIZE - 1, 0), (TILE_SIZE - 1, TILE_SIZE - 1), 1)

        self.rect = self.image.get_rect(topleft=(x, y))

class Spike(pygame.sprite.Sprite):
    """トゲ（障害物）- 三角形"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE // 2), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0)) # 完全に透過

        points = [
            (0, TILE_SIZE // 2),
            (TILE_SIZE // 2, 0),
            (TILE_SIZE, TILE_SIZE // 2)
        ]
        pygame.draw.polygon(self.image, SPIKE_COLOR, points)
        self.rect = self.image.get_rect(topleft=(x, y + TILE_SIZE // 2))

class Key(pygame.sprite.Sprite):
    """カギ"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(KEY_COLOR)
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))

class Door(pygame.sprite.Sprite):
    """トビラ（ゴール）"""
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
    
    player = None
    start_pos = (0, 0)
    
    map_height = len(level_map)
    map_width = len(level_map[0])
    
    for y, row in enumerate(level_map):
        for x, char in enumerate(row):
            world_x = x * TILE_SIZE
            world_y = y * TILE_SIZE
            
            if char == 'P':
                # 隣接タイルが 'P' かどうかをチェック
                has_neighbor_up = (y > 0 and level_map[y - 1][x] == 'P')
                has_neighbor_down = (y < map_height - 1 and level_map[y + 1][x] == 'P')
                has_neighbor_left = (x > 0 and level_map[y][x - 1] == 'P')
                has_neighbor_right = (x < map_width - 1 and level_map[y][x + 1] == 'P')
                
                p = Platform(world_x, world_y, 
                             has_neighbor_up, has_neighbor_down, 
                             has_neighbor_left, has_neighbor_right)
                platforms.add(p)
                all_sprites.add(p)
            elif char == 'S':
                s = Spike(world_x, world_y)
                spikes.add(s)
                all_sprites.add(s)
            elif char == 'K':
                k = Key(world_x, world_y)
                keys.add(k)
                all_sprites.add(k)
            elif char == 'D':
                d = Door(world_x, world_y)
                doors.add(d)
                all_sprites.add(d)
            elif char == '@':
                player_x = world_x + (TILE_SIZE - 30) // 2
                player_y = world_y + (TILE_SIZE - 30)
                start_pos = (player_x, player_y)
                player = Player(player_x, player_y)

    if player is None:
        print("エラー: プレイヤー(@)がマップにいません！")
        sys.exit()

    all_sprites.add(player)
    
    return player, start_pos, all_sprites, platforms, spikes, keys, doors

# --- メインゲーム処理 (カメラ・ズーム対応) ---
def main():
    pygame.init()
    # 実際のウィンドウ
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    # ゲームを描画する仮想スクリーン (小さい)
    game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    
    pygame.display.set_caption("Minimalism Prototype (Expanded)")
    clock = pygame.time.Clock()

    # --- レベルのセットアップ ---
    player, start_pos, all_sprites, platforms, spikes, keys, doors = setup_level(LEVEL_MAP)
    
    level_width = len(LEVEL_MAP[0]) * TILE_SIZE
    level_height = len(LEVEL_MAP) * TILE_SIZE
    
    camera_x = 0
    camera_y = 0

    while True:
        # --- イベント処理 (可変ジャンプ対応) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                    player.jump()
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                    player.cut_jump() # ジャンプキーを離したら上昇をカット

        # --- 更新処理 ---
        player.update(platforms)
        
        # --- カメラの更新 ---
        
        # X軸カメラ
        target_camera_x = player.rect.centerx - (GAME_WIDTH // 3) 
        if target_camera_x < 0:
            target_camera_x = 0
        if target_camera_x > level_width - GAME_WIDTH:
            target_camera_x = level_width - GAME_WIDTH
        camera_x += (target_camera_x - camera_x) / 20.0 # スムーズスクロール
        
        # Y軸カメラ
        target_camera_y = player.rect.centery - (GAME_HEIGHT // 2)
        if target_camera_y < 0:
            target_camera_y = 0
        if target_camera_y > level_height - GAME_HEIGHT:
            target_camera_y = level_height - GAME_HEIGHT
        camera_y += (target_camera_y - camera_y) / 20.0 # スムーズスクロール
        
        # --- 衝突判定 ---
        if pygame.sprite.spritecollide(player, spikes, False):
            print("ミス！リスタートします。")
            player.reset_position(*start_pos)
            player.has_key = False
            # 消えたカギを元に戻す
            for k in keys: 
                if not k in all_sprites:
                    all_sprites.add(k)
                    keys.add(k) # keys グループにも戻す

        key_hit = pygame.sprite.spritecollide(player, keys, True) # Trueでカギをグループから削除
        if key_hit:
            player.has_key = True
            print("カギを手に入れた！")

        if pygame.sprite.spritecollide(player, doors, False):
            if player.has_key:
                print("クリア！おめでとう！")
                pygame.quit()
                sys.exit()

        # --- 描画処理 (ズーム対応) ---
        
        # 1. 小さい仮想スクリーン (game_surface) を黒で塗りつぶす
        game_surface.fill(BLACK) 
        
        # 2. 仮想スクリーンに、カメラ座標を引いて全スプライトを描画
        for sprite in all_sprites:
            screen_x = sprite.rect.x - camera_x
            screen_y = sprite.rect.y - camera_y
            game_surface.blit(sprite.image, (screen_x, screen_y)) 
        
        # 3. 仮想スクリーンを、実際の画面サイズに引き伸ばして表示
        scaled_surface = pygame.transform.scale(game_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        
        # 4. 実際の画面を更新
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()