import pygame
import sys
import os
import random # ★ ランダム発射のために追加
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- 定数設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER_COLOR = (50, 50, 255)  # プレイヤー (青)
PLATFORM_COLOR = (100, 100, 100) # 足場 (灰色)
SPIKE_COLOR = (255, 50, 50)  # 障害物 (赤)
KEY_COLOR = (255, 215, 0) # カギ (黄)
DOOR_COLOR = (0, 200, 0)     # トビラ (緑)
ARROW_COLOR = (200, 200, 200) # 弓矢 (ライトグレー)
LAUNCHER_COLOR = (150, 50, 50) # 発射台 (茶色/赤茶色)

# 物理定数
GRAVITY = 0.8
JUMP_STRENGTH = -15
WALL_KICK_HORIZONTAL = 10 # 壁キック時の水平方向の力
WALL_KICK_VERTICAL = -12  # 壁キック時の垂直方向の力
PLAYER_SPEED = 5

# 弓矢の発射間隔 (ミリ秒)のランダム範囲を設定
MIN_ARROW_INTERVAL = 500  # 最小間隔 (0.5秒)
MAX_ARROW_INTERVAL = 1500 # 最大間隔 (1.5秒)

# --- プレイヤークラス (壁キック機能付き) ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.on_wall_left = False 
        self.on_wall_right = False 
        self.has_key = False

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
        else:
            self.vel_x = 0

        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10

        # X軸（横）の移動と壁との衝突判定
        self.rect.x += self.vel_x
        hit_list_x = pygame.sprite.spritecollide(self, platforms, False)
        self.on_wall_left = False
        self.on_wall_right = False
        
        for platform in hit_list_x:
            if self.vel_x > 0: 
                self.rect.right = platform.rect.left
                self.on_wall_right = True
            elif self.vel_x < 0: 
                self.rect.left = platform.rect.right
                self.on_wall_left = True
            self.vel_x = 0
            
        # 画面外に出ないように
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # Y軸（縦）の移動と衝突判定
        self.rect.y += self.vel_y
        
        hit_list_y = pygame.sprite.spritecollide(self, platforms, False)
        for platform in hit_list_y:
            if self.vel_y > 0: 
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
            elif self.vel_y < 0: 
                self.rect.top = platform.rect.bottom
                self.vel_y = 0

        # on_ground 判定
        self.rect.y += 1
        ground_hit_list = pygame.sprite.spritecollide(self, platforms, False)
        self.rect.y -= 1

        if len(ground_hit_list) > 0:
            self.on_ground = True
            self.on_wall_left = False
            self.on_wall_right = False
        else:
            self.on_ground = False

        # 壁に接している間は落下速度を緩める
        if not self.on_ground and (self.on_wall_left or self.on_wall_right):
            if self.vel_y > 3: 
                self.vel_y = 3


    def jump(self):
        # 1. 地上でのジャンプ
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH
            return
        
        # 2. 壁キック (回数制限なし)
        if self.on_wall_left:
            self.vel_y = WALL_KICK_VERTICAL
            self.vel_x = WALL_KICK_HORIZONTAL
            self.rect.x += 1 
            self.on_wall_left = False
            return
            
        if self.on_wall_right:
            self.vel_y = WALL_KICK_VERTICAL
            self.vel_x = -WALL_KICK_HORIZONTAL
            self.rect.x -= 1 
            self.on_wall_right = False
            return
        
    def reset_position(self, x, y):
        """プレイヤーを初期位置に戻す"""
        self.rect.topleft = (x, y)
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.on_wall_left = False
        self.on_wall_right = False
        self.has_key = False

# --- その他のオブジェクトクラス ---
class Platform(pygame.sprite.Sprite):
    """足場"""
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(PLATFORM_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))

class Spike(pygame.sprite.Sprite):
    """トゲ（障害物）"""
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(SPIKE_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))

class Key(pygame.sprite.Sprite):
    """カギ"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(KEY_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))

class Door(pygame.sprite.Sprite):
    """トビラ（ゴール）"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill(DOOR_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))

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

# --- メインゲーム処理 ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Minimalism Prototype - Wall Kick & Arrows")
    clock = pygame.time.Clock()

    # --- レベルのセットアップ ---
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    spikes = pygame.sprite.Group()
    arrows = pygame.sprite.Group()    # ★ 弓矢グループ
    launchers = pygame.sprite.Group() # ★ ランチャーグループ
    
    start_pos = (50, 450)
    player = Player(*start_pos)

    # 壁キックを試せるようにレベルを変更
    floor = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
    wall_left = Platform(0, 100, 40, 460)
    wall_right = Platform(SCREEN_WIDTH - 40, 100, 40, 460)
    p1 = Platform(200, 450, 100, 20)
    p2 = Platform(350, 250, 150, 20)
    door_platform = Platform(SCREEN_WIDTH - 150, 100, 150, 20) # ドアのための足場

    platforms.add(floor, wall_left, wall_right, p1, p2, door_platform)
    
    spike1 = Spike(250, 430, 20, 20)
    spikes.add(spike1)
    
    key = Key(420, 220)
    door = Door(SCREEN_WIDTH - 120, 40) # ドアを足場の上に配置

    all_sprites.add(player, platforms, spikes, key, door)
    keys_group = pygame.sprite.Group(key)
    # --- レベルセットアップここまで ---
    
    # --- 弓矢ランチャーの定義と配置 ---
    launcher1 = ArrowLauncher(SCREEN_WIDTH, 320, -1)     # 画面右端から左 (P2の高さ)
    launcher2 = ArrowLauncher(0, 150, 1)                 # 画面左端から右 (高めの位置)
    launcher4 = ArrowLauncher(SCREEN_WIDTH, SCREEN_HEIGHT - 70, -1) # 右端、地面近く

    launcher_list = [launcher1, launcher2, launcher4]
    
    # 全てのランチャーをグループに追加して描画する
    launchers.add(*launcher_list)
    all_sprites.add(*launcher_list)

    # --- ランダム発射の管理変数 ---
    current_time = pygame.time.get_ticks()
    # 次の弓矢が発射される時刻
    next_arrow_launch_time = current_time + random.randint(MIN_ARROW_INTERVAL, MAX_ARROW_INTERVAL)


    running = True
    while running:
        # --- イベント処理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                    player.jump()

        # --- 更新処理 ---
        
        # ★ ランダム発射のロジック
        current_time = pygame.time.get_ticks()
        
        if current_time > next_arrow_launch_time:
            # 1. ランチャーをランダムに選択
            selected_launcher = random.choice(launcher_list)
            
            # 2. 弓矢を生成 (ランチャーの座標と向きを使用)
            new_arrow = Arrow(
                selected_launcher.rect.x, 
                selected_launcher.rect.y + selected_launcher.rect.height // 2 - 4,
                selected_launcher.direction
            )
            arrows.add(new_arrow)
            all_sprites.add(new_arrow) 
            
            # 3. 次の発射時間をランダムに更新
            random_interval = random.randint(MIN_ARROW_INTERVAL, MAX_ARROW_INTERVAL)
            next_arrow_launch_time = current_time + random_interval

        player.update(platforms)
        arrows.update() # ★ 弓矢を移動させる

        # トゲとの衝突判定
        if pygame.sprite.spritecollide(player, spikes, False):
            print("ミス！リスタートします。")
            player.reset_position(*start_pos)
            # カギのリセット
            if not key.alive():
                key = Key(420, 220)
                all_sprites.add(key)
                keys_group.add(key)
            else:
                player.has_key = False

        # ★ 弓矢との衝突判定 (ゲームオーバー)
        if pygame.sprite.spritecollide(player, arrows, True): 
            print("弓矢に当たった！リスタートします。")
            player.reset_position(*start_pos)
            # カギのリセット
            if not key.alive():
                key = Key(420, 220)
                all_sprites.add(key)
                keys_group.add(key)
            else:
                player.has_key = False


        # カギとの衝突判定
        key_hit_list = pygame.sprite.spritecollide(player, keys_group, True)
        if key_hit_list:
            player.has_key = True
            print("カギを手に入れた！")

        # トビラとの衝突判定
        if pygame.sprite.collide_rect(player, door):
            if player.has_key:
                print("クリア！おめでとう！")
                running = False
            # else:
            #     pass

        # --- 描画処理 ---
        screen.fill(BLACK)
        all_sprites.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()