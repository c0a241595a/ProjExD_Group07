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
PLAYER_COLOR = (50, 50, 255) # プレイヤー (青)
PLATFORM_COLOR = (100, 100, 100) # 足場 (灰色)
SPIKE_COLOR = (255, 50, 50)  # 障害物 (赤)
KEY_COLOR = (255, 215, 0) # カギ (黄)
DOOR_COLOR = (0, 200, 0) # トビラ (緑)
ARROW_COLOR = (200, 200, 200) # 弓矢 (ライトグレー)
LAUNCHER_COLOR = (150, 50, 50) # 発射台 (茶色/赤茶色)

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

# --- プレイヤークラス (壁キック対応、クールダウン付き) ---
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
        
        # 壁キック用のフラグ
        self.on_wall = 0 
        
        # ★壁キック用クールダウン追加★
        self.wall_jump_cooldown = 0
        self.WALL_JUMP_COOLDOWN_FRAMES = 10 # 10フレーム (約0.16秒) 入力を無視

    def check_side_collision(self, platforms):
        """
        X軸の衝突判定を行い、壁接触フラグ (self.on_wall) を設定する
        """
        # 左右に移動
        self.rect.x += self.vel_x
        
        hit_list = pygame.sprite.spritecollide(self, platforms, False)
        self.on_wall = 0 # 初期化
        
        for platform in hit_list:
            # 衝突した場合は、位置を壁の外側に強制的に戻す
            if self.vel_x > 0: # 右に移動中に衝突 (右壁に接触)
                self.rect.right = platform.rect.left
                self.on_wall = 1 # 右壁に接触
            elif self.vel_x < 0: # 左に移動中に衝突 (左壁に接触)
                self.rect.left = platform.rect.right
                self.on_wall = -1 # 左壁に接触

    def apply_gravity(self):
        """重力を適用し、最大落下速度を制限する"""
        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
    
    
    def update(self, platforms):
        
        # ★クールダウンを処理★
        if self.wall_jump_cooldown > 0:
            self.wall_jump_cooldown -= 1
        
        keys = pygame.key.get_pressed()

        # 1. 左右の入力
        # クールダウン中の場合は、入力による横速度変更をスキップ
        if self.wall_jump_cooldown == 0:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.vel_x = -PLAYER_SPEED
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.vel_x = PLAYER_SPEED
            else:
                self.vel_x = 0

        # 2. X軸（横）の移動と衝突判定
        self.check_side_collision(platforms)

        # 3. 重力と壁ずり落ち
        if not self.on_ground and self.on_wall != 0 and self.vel_y > 0:
            # 壁に張り付いている時、落下速度を遅くする (壁ずり落ち)
            self.vel_y = min(self.vel_y, WALL_SLIDE_SPEED)
        else:
            self.apply_gravity()
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

        # 4. Y軸（縦）の移動と衝突判定（足場）
        self.rect.y += self.vel_y
        hit_list = pygame.sprite.spritecollide(self, platforms, False)
        
        for platform in hit_list:
            if self.vel_y > 0: # 下に落ちている時 (着地)
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
            elif self.vel_y < 0: 
                self.rect.top = platform.rect.bottom
                self.vel_y = 0

        # 5. on_ground 判定
        self.rect.y += 1
        ground_hit_list = pygame.sprite.spritecollide(self, platforms, False)
        self.rect.y -= 1
        self.on_ground = len(ground_hit_list) > 0

        # 6. 画面外に出ないように
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        if len(ground_hit_list) > 0:
            self.on_ground = True
            self.on_wall_left = False
            self.on_wall_right = False
        else:
            self.on_ground = False



    def jump(self):
        """通常ジャンプと壁キックを処理する"""
        if self.on_ground:
            # 地上にいる時: 通常ジャンプ
            self.vel_y = JUMP_STRENGTH
        elif self.on_wall != 0:
            # 空中かつ壁に接触している時: 壁キック
            
            # 縦方向の速度 (上方向へ)
            self.vel_y = WALL_JUMP_STRENGTH_Y 
            
            # 横方向の速度 (壁キックは壁から離れる方向に強く)
            self.vel_x = -self.on_wall * WALL_JUMP_STRENGTH_X
            
            # ★クールダウンをセット★
            self.wall_jump_cooldown = self.WALL_JUMP_COOLDOWN_FRAMES
            
            # 壁キック後は壁から離れるため、on_wall をリセット
            self.on_wall = 0
            
            return
        
        
        
    def reset_position(self, x, y):
        """プレイヤーを初期位置に戻す"""
        self.rect.topleft = (x, y)
        self.vel_y = 0
        self.on_ground = False
        self.has_key = False
        self.wall_jump_cooldown = 0 # クールダウンもリセット

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
    pygame.display.set_caption("Minimalism Prototype (Wall Kick & Arrows)")
    clock = pygame.time.Clock()

    # --- レベルのセットアップ ---
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    spikes = pygame.sprite.Group()
    arrows = pygame.sprite.Group()    # ★ 弓矢グループ
    launchers = pygame.sprite.Group() # ★ ランチャーグループ
    
    start_pos = (50, 450)
    player = Player(*start_pos)

    # 足場を作成
    floor = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
    p1 = Platform(200, 450, 100, 20)
    p2 = Platform(400, 350, 150, 20)
    
    # 壁キックを試しやすいように、左と右に大きな壁を追加
    left_wall = Platform(0, 0, 40, SCREEN_HEIGHT - 40) # 床以外は壁
    right_wall = Platform(SCREEN_WIDTH - 40, 0, 40, SCREEN_HEIGHT - 40)
    
    platforms.add(floor, p1, p2, left_wall, right_wall) # 壁を追加
    
    # 障害物を作成
    spike1 = Spike(250, 430, 20, 20) # p1の上
    spikes.add(spike1)
    
    # アイテムとゴールを作成
    key = Key(450, 320) # p2の上
    door = Door(SCREEN_WIDTH - 80, SCREEN_HEIGHT - 100) # 床の右端

    all_sprites.add(player, platforms, spikes, key, door)
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


    while True:
        # --- イベント処理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                    player.jump() # on_ground または on_wall のときに実行される

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
            # カギもリセット (もし取得済みだったら)
            if not key in all_sprites:
                # 既存のKeyオブジェクトを再利用してリセット
                key = Key(450, 320)
                all_sprites.add(key)

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
        # keyがall_spritesに含まれているかチェックしてから衝突判定
        if key in all_sprites and pygame.sprite.collide_rect(player, key):
            player.has_key = True
            key.kill() # カギを消す
            print("カギを手に入れた！")

        # トビラとの衝突判定
        if pygame.sprite.collide_rect(player, door):
            if player.has_key:
                print("クリア！おめでとう！")
                pygame.quit()
                sys.exit()
            else:
                pass

        # --- 描画処理 ---
        screen.fill(BLACK) # 画面を黒で塗りつぶす
        all_sprites.draw(screen) # 全てのスプライトを描画
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()