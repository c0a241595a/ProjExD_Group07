import pygame
import sys
import os
import random
import math

# スクリプトのディレクトリをワーキングディレクトリに設定
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))
else:
    # __file__ が定義されていない環境（例: IDLE）のためのフォールバック
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))


# --- 定数設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# ゲームの「見える範囲」 (カメラのズーム設定)
GAME_WIDTH = 640
GAME_HEIGHT = 480

FPS = 60
TILE_SIZE = 40  # 1マスのサイズ

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
# ★★★ 背景色を暗い紺色に変更 ★★★
GAME_BACKGROUND_COLOR = (10, 10, 25)

# ★★★ 星空用の色設定 ★★★
STAR_COLORS = [(255, 255, 255), (200, 200, 200), (255, 255, 220)]
NUM_STARS = 300  # 星の数
PARALLAX_FACTOR = 0.5  # 星のスクロール速度 (0.5 = カメラの半分の速度)

# プレイヤーの新しい色
PLAYER_FILL_COLOR = (60, 160, 220)  # 明るい青
PLAYER_EYE_COLOR = (40, 40, 40)  # 目 (背景色と同じ)

SPIKE_COLOR = (230, 80, 90)  # 障害物 (赤)
KEY_COLOR = (255, 215, 0)  # カギ (黄)
DOOR_COLOR = (0, 200, 0)  # トビラ (緑)
GRAVITY_SWITCHER_COLOR = (200, 50, 200)  # 重力スイッチの色 (紫)
ARROW_COLOR = (200, 200, 200)  # 弓矢 (ライトグレー)
LAUNCHER_COLOR = (150, 50, 50)  # 発射台 (茶色/赤茶色)
JUMPPAD_COLOR = (200, 0, 255)  # ジャンプ台 (紫)

# ★★★ 足場の新しい色 (灰色系統) ★★★
PLATFORM_SIDE_COLOR = (70, 70, 70)  # 暗い灰色 (側面)
PLATFORM_TOP_COLOR = (110, 110, 110)  # 明るい灰色 (上面)
PLATFORM_TOP_THICKNESS = 8  # 上面の厚さ (ピクセル)

# ★★★ マインクラフト風の「規則的なまだら模様」用パレット ★★★
# 側面 (PLATFORM_SIDE_COLOR = (70, 70, 70) の周辺色)
SIDE_PATTERN_PALETTE = [(65, 65, 65), (70, 70, 70), (75, 75, 75), (80, 80, 80)]
# 標準上面 (PLATFORM_TOP_COLOR = (110, 110, 110) の周辺色)
TOP_PATTERN_PALETTE = [
    (105, 105, 105),
    (110, 110, 110),
    (115, 115, 115),
    (120, 120, 120),
]

# ★★★ 追加：紫色の上面パレット ★★★
PURPLE_TOP_COLOR = (150, 80, 180)  # 紫色のベース
PURPLE_TOP_PATTERN_PALETTE = [
    (145, 75, 175),
    (150, 80, 180),
    (155, 85, 185),
    (160, 90, 190),
]

# ★★★ 追加：黄色の上面パレット ★★★
YELLOW_TOP_COLOR = (220, 180, 70)  # 黄色のベース
YELLOW_TOP_PATTERN_PALETTE = [
    (215, 175, 65),
    (220, 180, 70),
    (225, 185, 75),
    (230, 190, 80),
]

# ★★★ 追加：水色の上面パレット ★★★
CYAN_TOP_COLOR = (70, 180, 200)  # 水色のベース
CYAN_TOP_PATTERN_PALETTE = [
    (65, 175, 195),
    (70, 180, 200),
    (75, 185, 205),
    (80, 190, 210),
]

# ★★★ 追加：オレンジ色の上面パレット ★★★
ORANGE_TOP_COLOR = (240, 140, 60)  # オレンジ色のベース
ORANGE_TOP_PATTERN_PALETTE = [
    (235, 135, 55),
    (240, 140, 60),
    (245, 145, 65),
    (250, 150, 70),
]

# ★★★ 追加：赤色の上面パレット ★★★
RED_TOP_COLOR = (220, 70, 70)  # 赤色のベース
RED_TOP_PATTERN_PALETTE = [(215, 65, 65), (220, 70, 70), (225, 75, 75), (230, 80, 80)]

# ★★★ 追加：青色の上面パレット ★★★
BLUE_TOP_COLOR = (80, 100, 220)  # 青色のベース
BLUE_TOP_PATTERN_PALETTE = [
    (75, 95, 215),
    (80, 100, 220),
    (85, 105, 225),
    (90, 110, 230),
]

# ★★★ 追加：緑色の上面パレット ★★★
GREEN_TOP_COLOR = (90, 190, 90)  # 緑色のベース
GREEN_TOP_PATTERN_PALETTE = [
    (85, 185, 85),
    (90, 190, 90),
    (95, 195, 95),
    (100, 200, 100),
]
# ★★★ ここまで ★★★


# ★★★ ブースターの新しい色 (灰色系統のアクセントカラー) ★★★
BOOSTER_SIDE_COLOR = (120, 120, 60)  # 暗い黄土色 (側面)
BOOSTER_TOP_COLOR = (180, 180, 80)  # 明るい黄土色 (上面)
BOOSTER_GRASS_COLOR = (200, 200, 100)  # 黄土色の草
# ★★★ ここまで ★★★


# 物理定数
GRAVITY = 0.4
JUMP_STRENGTH = -12
PLAYER_SPEED = 5
# 壁キック用の定数
WALL_JUMP_STRENGTH_Y = -15  # 壁キックの縦方向の強さ
WALL_JUMP_STRENGTH_X = 7  # 壁キックの横方向の強さ（移動速度より大きくする）
WALL_SLIDE_SPEED = 1  # 壁ずり落ちる速度

# 弓矢の発射間隔 (ミリ秒)のランダム範囲を設定
MIN_ARROW_INTERVAL = 1500  # 最小間隔 (1.5秒)
MAX_ARROW_INTERVAL = 3000  # 最大間隔 (3.0秒)

MOVE_SPEED = 5
MAX_SPEED = 6
ACCELERATION = 0.4
FRICTION_FORCE = 0.1  # ★滑りを増やすため 0.1 に変更


# ヘルパー関数
def get_angle_from_gravity(direction):
    if direction == "UP":
        return 180
    return 0


# 物理定数 (慣性・摩擦あり)
GRAVITY = 0.4  # 重力
JUMP_STRENGTH = -10  # ジャンプ力
MAX_SPEED = 6  # プレイヤーの最高速度
ACCELERATION = 0.4  # 加速の度合い
FRICTION_FORCE = 0.1  # 摩擦力 (★滑りを増やすため 0.1)

# --- ステージの設計図 (8色に増強、灰色Pは廃止) ---
LEVEL_MAP = [
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVCCCCCCCCCCCCCCCCCCCC",  # 0
    "A          SSS   VMM V    S                 SSC",  # 1
    "V                               F       FF    C",  # 2
    "V   V     VVVVV            CCCCCCCCCCCCCCC  CCC",  # 3
    "V   V         S            CSS               SC",  # 4
    "VSS V                      C                  C",  # 5
    "VVV VVVVVVVVVVVVVVVVV      C     LLLLLLLLLLLLLL",  # 6
    "V         VSSSSSSSSSOOOOOOOO     SA        MM L",  # 7
    "V         V                       L           L",  # 8
    "V     G   V   OO       OOOOOOOOOOOL           L",  # 9
    "V     VVVVV            Y YYYYYYYY Y    LLLL   L",  # 10
    "Y     YSSSYYY     YYYYYY YYYYYYYY Y    L      L",  # 11 (YSSSYYY に変更)
    "Y     Y            YA                  L      L",  # 12
    "Y     YK               SSSSSSSSSSSS    A      L",  # 13
    "Y     YYYYYYYYYYYYYYYYYYYYYYYYYYYYY    L      L",  # 14
    "Y     Y                           Y    LF     L",  # 15
    "Y     Y                           YYYYYLLLL  DC",  # 16
    "R     R                                   LLLLL",  # 17
    "A                                 RRRRR     F R",  # 18
    "RBBBBBRRRRRRRRRRRRRRRRRRRRRRRRRRRRR   RRR     R",  # 19
    "L                                       RRR   L",  # 20
    "L                                             L",  # 21
    "E@       S     S     SS    S       SSS       SE",  # 22 (スタート)
    "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE",  # 23
]


# --- プレイヤークラス (慣性・角丸・可変ジャンプ対応) ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        # ★ 1. 標準 (下向き重力) の画像を生成
        self.image_down = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.image_down.fill((0, 0, 0, 0))  # 完全に透過

        # 本体 (明るい青) を角丸で描画
        body_rect = self.image_down.get_rect()
        pygame.draw.rect(self.image_down, PLAYER_FILL_COLOR, body_rect, border_radius=4)

        # 目を描画 (2つの小さな四角)
        eye_width = 4
        eye_height = 5
        eye_y = 8
        left_eye_rect = pygame.Rect(8, eye_y, eye_width, eye_height)
        right_eye_rect = pygame.Rect(30 - 8 - eye_width, eye_y, eye_width, eye_height)

        pygame.draw.rect(self.image_down, PLAYER_EYE_COLOR, left_eye_rect)
        pygame.draw.rect(self.image_down, PLAYER_EYE_COLOR, right_eye_rect)

        # ★ 2. 上向き重力用の画像 (上下反転) を生成
        self.image_up = pygame.transform.flip(self.image_down, False, True)

        # ★ 3. 初期イメージを設定
        self.image = self.image_down

        self.rect = self.image.get_rect(topleft=(x, y))

        # マスクは 30x30 の四角として共通
        mask_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        mask_surface.fill((255, 255, 255))
        self.mask = pygame.mask.from_surface(mask_surface)

        # float型の正確な位置を保持
        self.true_x = float(self.rect.x)
        self.true_y = float(self.rect.y)

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
        self.WALL_JUMP_COOLDOWN_FRAMES = 10  # 10フレーム (約0.16秒) 入力を無視

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

        if self.wall_jump_cooldown == 0:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                target_vel_x = -MOVE_SPEED * self.speed_multiplier
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                target_vel_x = MOVE_SPEED * self.speed_multiplier

        if target_vel_x != 0:  # 加速
            self.vel_x += (target_vel_x - self.vel_x) * ACCELERATION
        else:  # 摩擦
            self.vel_x *= 1.0 - FRICTION_FORCE

        # C. 最高速度制限
        if self.vel_x > MAX_SPEED:
            self.vel_x = MAX_SPEED
        elif self.vel_x < -MAX_SPEED:
            self.vel_x = -MAX_SPEED

        if abs(self.vel_x) < 0.1:
            self.vel_x = 0
        self.vel_x = max(
            -MAX_SPEED * self.speed_multiplier,
            min(self.vel_x, MAX_SPEED * self.speed_multiplier),
        )

        # --- 3. Y軸の重力と壁ずり落ち ---
        if not self.on_ground:
            if self.on_wall != 0 and self.vel_y > 0 and current_gravity == "DOWN":
                self.vel_y = min(self.vel_y + GRAVITY, WALL_SLIDE_SPEED)
            elif self.on_wall != 0 and self.vel_y < 0 and current_gravity == "UP":
                self.vel_y = max(self.vel_y - GRAVITY, -WALL_SLIDE_SPEED)
            else:
                if current_gravity == "DOWN":
                    self.vel_y += GRAVITY
                elif current_gravity == "UP":
                    self.vel_y -= GRAVITY
                self.vel_y = max(-1000, min(self.vel_y, 10))

        # --- 4. X軸（横）の移動と衝突判定 ---
        self.true_x += self.vel_x
        self.rect.x = int(self.true_x)

        hit_list_x = pygame.sprite.spritecollide(self, platforms, False)

        self.on_wall = 0
        self.on_wall_right = False
        self.on_wall_left = False

        for platform in hit_list_x:
            if self.vel_x > 0:  # 右に移動中
                self.rect.right = platform.rect.left
                self.on_wall_right = True
                self.on_wall = 1  # 右壁
            elif self.vel_x < 0:  # 左に移動中
                self.rect.left = platform.rect.right
                self.on_wall_left = True
                self.on_wall = -1  # 左壁

            self.true_x = float(self.rect.x)
            self.vel_x = 0

        # --- 5. Y軸（縦）の移動と衝突判定 (貫通対策ロジック) ---
        remaining_y = self.vel_y
        sign = 1 if remaining_y > 0 else -1
        # プレイヤーの高さ (30) - 1 = 29
        max_step_size = self.rect.height - 1
        if max_step_size <= 0:
            max_step_size = 1  # ゼロ除算回避

        while abs(remaining_y) > 0.001:
            step = min(abs(remaining_y), max_step_size) * sign
            self.true_y += step
            self.rect.y = int(self.true_y)

            hit_list_y = pygame.sprite.spritecollide(self, platforms, False)

            if hit_list_y:
                if current_gravity == "DOWN":
                    if self.vel_y > 0:  # 着地
                        best_platform = min(hit_list_y, key=lambda p: p.rect.top)
                        self.rect.bottom = best_platform.rect.top
                    elif self.vel_y < 0:  # 頭をぶつけた
                        best_platform = max(hit_list_y, key=lambda p: p.rect.bottom)
                        self.rect.top = best_platform.rect.bottom
                elif current_gravity == "UP":
                    if self.vel_y < 0:  # 着地 (天井へ)
                        best_platform = max(hit_list_y, key=lambda p: p.rect.bottom)
                        self.rect.top = best_platform.rect.bottom
                    elif self.vel_y > 0:  # 頭をぶつけた (床へ)
                        best_platform = min(hit_list_y, key=lambda p: p.rect.top)
                        self.rect.bottom = best_platform.rect.top

                self.true_y = float(self.rect.y)
                self.vel_y = 0
                remaining_y = 0.0
                break

            remaining_y -= step

        # --- 6. 接地判定 ---
        self.on_ground = False
        self.standing_on.clear()

        check_rect = self.rect.copy()
        if current_gravity == "DOWN":
            check_rect.y += 1
        elif current_gravity == "UP":
            check_rect.y -= 1

        ground_hit_list = []
        for platform in platforms:
            if check_rect.colliderect(platform.rect):
                ground_hit_list.append(platform)

        if len(ground_hit_list) > 0:
            self.on_ground = True
            self.standing_on = ground_hit_list

        # ★ 7. 重力に応じて画像を変更
        if current_gravity == "DOWN":
            self.image = self.image_down
        elif current_gravity == "UP":
            self.image = self.image_up

    def jump(self, current_gravity):
        keys = pygame.key.get_pressed()

        # 1. 地上ジャンプ
        if self.on_ground:
            power = self.jump_multiplier
            if current_gravity == "DOWN":
                self.vel_y = JUMP_STRENGTH * power
            elif current_gravity == "UP":
                self.vel_y = -JUMP_STRENGTH * power

        # 2. 壁キック
        elif self.on_wall != 0:
            is_pushing_into_wall = False
            if self.on_wall == -1 and (keys[pygame.K_LEFT] or keys[pygame.K_a]):
                is_pushing_into_wall = True
            elif self.on_wall == 1 and (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                is_pushing_into_wall = True

            if is_pushing_into_wall:
                if current_gravity == "DOWN":
                    self.vel_y = WALL_JUMP_STRENGTH_Y
                else:
                    self.vel_y = -WALL_JUMP_STRENGTH_Y
                self.vel_x = -self.on_wall * WALL_JUMP_STRENGTH_X
                self.wall_jump_cooldown = self.WALL_JUMP_COOLDOWN_FRAMES
                self.on_wall = 0

    def cut_jump(self, current_gravity):
        if current_gravity == "DOWN":
            if self.vel_y < 0:  # 上昇中 (下向き重力)
                self.vel_y *= 0.4
        elif current_gravity == "UP":
            if self.vel_y > 0:  # "上昇"中 (上向き重力)
                self.vel_y *= 0.4

    def reset_position(self, x, y):
        self.rect.topleft = (x, y)
        self.true_x = float(x)
        self.true_y = float(y)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.has_key = False
        self.speed_multiplier = 1.0
        self.jump_multiplier = 1.0
        self.standing_on.clear()
        self.wall_jump_cooldown = 0
        # ★ リセット時は必ず下向き重力から開始する想定
        self.image = self.image_down


# --- その他のオブジェクトクラス ---


# ▼▼▼ Platform クラス (ベースクラス) ▼▼▼
class Platform(pygame.sprite.Sprite):
    """足場 (マインクラフト風の規則的なまだら模様) - ベースクラス"""

    def __init__(
        self,
        x,
        y,
        up,
        down,
        left,
        right,
        top_color=PLATFORM_TOP_COLOR,
        top_palette=TOP_PATTERN_PALETTE,
    ):

        super().__init__()

        # 1. 隣接情報を保存
        self.has_neighbor_up = up
        self.has_neighbor_down = down
        self.has_neighbor_left = left
        self.has_neighbor_right = right

        # 2. 3種類の画像をあらかじめ生成する

        # (A) 側面のみ (ベース)
        self.image_side = self.create_side_image()

        # (B) 上面画像 (image_top)
        if not self.has_neighbor_up:
            self.image_top = self.create_top_image(
                self.image_side.copy(), top_color, top_palette
            )
        else:
            self.image_top = self.image_side

        # (C) 下面画像 (image_bottom)
        if not self.has_neighbor_down:
            self.image_bottom = self.create_bottom_image(
                self.image_side.copy(), top_color, top_palette
            )
        else:
            self.image_bottom = self.image_side

        # 3. 初期イメージを設定 (重力は下向きスタート)
        self.image = self.image_top
        self.rect = self.image.get_rect(topleft=(x, y))

    def create_side_image(self):
        """側面のまだら模様だけの画像を生成して返す"""
        image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        image.fill(PLATFORM_SIDE_COLOR)
        PIXEL_GRID_SIZE_SIDE = 5
        for y_pos in range(0, TILE_SIZE, PIXEL_GRID_SIZE_SIDE):
            for x_pos in range(0, TILE_SIZE, PIXEL_GRID_SIZE_SIDE):
                color = random.choice(SIDE_PATTERN_PALETTE)
                pygame.draw.rect(
                    image,
                    color,
                    (x_pos, y_pos, PIXEL_GRID_SIZE_SIDE, PIXEL_GRID_SIZE_SIDE),
                )
        return image

    def create_top_image(self, base_image, top_color, top_palette):
        """受け取った画像に「上面」を描画して返す"""
        top_rect = pygame.Rect(0, 0, TILE_SIZE, PLATFORM_TOP_THICKNESS)
        pygame.draw.rect(base_image, top_color, top_rect)

        PIXEL_GRID_SIZE_TOP = 4
        for y_pos in range(0, PLATFORM_TOP_THICKNESS, PIXEL_GRID_SIZE_TOP):
            for x_pos in range(0, TILE_SIZE, PIXEL_GRID_SIZE_TOP):
                color = random.choice(top_palette)
                pygame.draw.rect(
                    base_image,
                    color,
                    (x_pos, y_pos, PIXEL_GRID_SIZE_TOP, PIXEL_GRID_SIZE_TOP),
                )
        return base_image

    def create_bottom_image(self, base_image, top_color, top_palette):
        """受け取った画像に「下面」を描画して返す"""
        bottom_y = TILE_SIZE - PLATFORM_TOP_THICKNESS
        bottom_rect = pygame.Rect(0, bottom_y, TILE_SIZE, PLATFORM_TOP_THICKNESS)
        pygame.draw.rect(base_image, top_color, bottom_rect)

        PIXEL_GRID_SIZE_TOP = 4
        for y_pos_rel in range(0, PLATFORM_TOP_THICKNESS, PIXEL_GRID_SIZE_TOP):
            for x_pos in range(0, TILE_SIZE, PIXEL_GRID_SIZE_TOP):
                color = random.choice(top_palette)
                draw_y = bottom_y + y_pos_rel  # 描画Y座標
                pygame.draw.rect(
                    base_image,
                    color,
                    (x_pos, draw_y, PIXEL_GRID_SIZE_TOP, PIXEL_GRID_SIZE_TOP),
                )
        return base_image

    def update(self, current_gravity):
        """重力方向に応じて表示する画像を切り替える"""
        if current_gravity == "DOWN":
            self.image = self.image_top
        elif current_gravity == "UP":
            self.image = self.image_bottom


# ▲▲▲ Platform クラス ここまで ▲▲▲


# ★★★ PurplePlatform クラス (紫色の上面) ★★★
class PurplePlatform(Platform):
    """上面が紫色の足場"""

    def __init__(self, x, y, up, down, left, right):
        super().__init__(
            x,
            y,
            up,
            down,
            left,
            right,
            top_color=PURPLE_TOP_COLOR,
            top_palette=PURPLE_TOP_PATTERN_PALETTE,
        )


# ★★★ YellowPlatform クラス (黄色の上面) ★★★
class YellowPlatform(Platform):
    """上面が黄色の足場"""

    def __init__(self, x, y, up, down, left, right):
        super().__init__(
            x,
            y,
            up,
            down,
            left,
            right,
            top_color=YELLOW_TOP_COLOR,
            top_palette=YELLOW_TOP_PATTERN_PALETTE,
        )


# ★★★ CyanPlatform クラス (水色の上面) ★★★
class CyanPlatform(Platform):
    """上面が水色の足場"""

    def __init__(self, x, y, up, down, left, right):
        super().__init__(
            x,
            y,
            up,
            down,
            left,
            right,
            top_color=CYAN_TOP_COLOR,
            top_palette=CYAN_TOP_PATTERN_PALETTE,
        )


# ★★★ OrangePlatform クラス (オレンジ色の上面) ★★★
class OrangePlatform(Platform):
    """上面がオレンジ色の足場"""

    def __init__(self, x, y, up, down, left, right):
        super().__init__(
            x,
            y,
            up,
            down,
            left,
            right,
            top_color=ORANGE_TOP_COLOR,
            top_palette=ORANGE_TOP_PATTERN_PALETTE,
        )


# ★★★ RedPlatform クラス (赤色の上面) ★★★
class RedPlatform(Platform):
    """上面が赤色の足場"""

    def __init__(self, x, y, up, down, left, right):
        super().__init__(
            x,
            y,
            up,
            down,
            left,
            right,
            top_color=RED_TOP_COLOR,
            top_palette=RED_TOP_PATTERN_PALETTE,
        )


# ★★★ BluePlatform クラス (青色の上面) ★★★
class BluePlatform(Platform):
    """上面が青色の足場"""

    def __init__(self, x, y, up, down, left, right):
        super().__init__(
            x,
            y,
            up,
            down,
            left,
            right,
            top_color=BLUE_TOP_COLOR,
            top_palette=BLUE_TOP_PATTERN_PALETTE,
        )


# ★★★ GreenPlatform クラス (緑色の上面) ★★★
class GreenPlatform(Platform):
    """上面が緑色の足場"""

    def __init__(self, x, y, up, down, left, right):
        super().__init__(
            x,
            y,
            up,
            down,
            left,
            right,
            top_color=GREEN_TOP_COLOR,
            top_palette=GREEN_TOP_PATTERN_PALETTE,
        )


# ▼▼▼ 修正後の BoosterPlatform クラス ▼▼▼
class BoosterPlatform(Platform):
    def __init__(self, x, y, up, down, left, right):
        # 1. 親(Platform)の __init__ を呼んで、灰色の側面・灰色の上下 を設定
        super().__init__(x, y, up, down, left, right)

        # 2. 側面の画像を黄土色で再生成
        self.image_side = (
            self.create_side_image()
        )  # (BoosterPlatform に create_side_image を追加)

        # 3. 上面画像を草付きで再生成
        if not self.has_neighbor_up:
            self.image_top = self.create_top_image_with_grass(self.image_side.copy())
        else:
            self.image_top = self.image_side

        # 4. 下面画像を草付きで再生成
        if not self.has_neighbor_down:
            self.image_bottom = self.create_bottom_image_with_grass(
                self.image_side.copy()
            )
        else:
            self.image_bottom = self.image_side

        # 5. 初期イメージを更新
        self.image = self.image_top

    def create_side_image(self):
        """(Override) 側面の画像を黄土色で生成"""
        image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        image.fill(BOOSTER_SIDE_COLOR)
        # (黄土色用のまだら模様パレットがあってもよいが、今回は省略)
        return image

    def create_top_image_with_grass(self, base_image):
        """上面（黄土色＋草）を描画"""
        top_rect = pygame.Rect(0, 0, TILE_SIZE, PLATFORM_TOP_THICKNESS)
        pygame.draw.rect(base_image, BOOSTER_TOP_COLOR, top_rect)

        for i in range(2, TILE_SIZE - 2, 6):
            grass_height = random.randint(3, 5)
            grass_y = PLATFORM_TOP_THICKNESS - grass_height
            grass_rect = pygame.Rect(i, grass_y, 2, grass_height)
            pygame.draw.rect(base_image, BOOSTER_GRASS_COLOR, grass_rect)
        return base_image

    def create_bottom_image_with_grass(self, base_image):
        """下面（黄土色＋草）を描画"""
        bottom_y = TILE_SIZE - PLATFORM_TOP_THICKNESS
        bottom_rect = pygame.Rect(0, bottom_y, TILE_SIZE, PLATFORM_TOP_THICKNESS)
        pygame.draw.rect(base_image, BOOSTER_TOP_COLOR, bottom_rect)

        for i in range(2, TILE_SIZE - 2, 6):
            grass_height = random.randint(3, 5)
            grass_y = TILE_SIZE - grass_height  # 下端から生える
            grass_rect = pygame.Rect(i, grass_y, 2, grass_height)
            pygame.draw.rect(base_image, BOOSTER_GRASS_COLOR, grass_rect)
        return base_image


# ▲▲▲ 修正後の BoosterPlatform クラス ここまで ▲▲▲


class GravitySwitcher(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((25, 25))
        self.image.fill(GRAVITY_SWITCHER_COLOR)
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))


class Spike(pygame.sprite.Sprite):
    """トゲ（障害物）- 三角形 (4方向対応)"""

    def __init__(self, x, y, orientation="UP"):
        super().__init__()

        # 1. 40x40 の透明なベースイメージを作成
        base_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        base_image.fill((0, 0, 0, 0))
        self.orientation = orientation

        # 2. 40x40 のベースに三角形を描画
        if self.orientation == "DOWN":  # 天井トゲ (タイルの上半分に描画)
            points = [
                (0, 0),  # Top-Left
                (TILE_SIZE, 0),  # Top-Right
                (TILE_SIZE // 2, TILE_SIZE // 2),  # Center-Tip (下向きの先端)
            ]
        elif self.orientation == "LEFT":  # 右壁トゲ (タイルの左半分に描画)
            points = [
                (0, 0),  # Top-Left
                (0, TILE_SIZE),  # Bottom-Left
                (TILE_SIZE // 2, TILE_SIZE // 2),  # Center-Tip (左向きの先端)
            ]
        elif self.orientation == "RIGHT":  # 左壁トゲ (タイルの右半分に描画)
            points = [
                (TILE_SIZE, 0),  # Top-Right
                (TILE_SIZE, TILE_SIZE),  # Bottom-Right
                (TILE_SIZE // 2, TILE_SIZE // 2),  # Center-Tip (右向きの先端)
            ]
        else:  # "UP" (床トゲ)
            points = [
                (0, TILE_SIZE),  # Bottom-Left (Y=40)
                (TILE_SIZE, TILE_SIZE),  # Bottom-Right (Y=40)
                (TILE_SIZE // 2, TILE_SIZE // 2),  # Center-Tip (Y=20) (先端)
            ]

        pygame.draw.polygon(base_image, SPIKE_COLOR, points)

        # 3. 40x40 の original_image を保存
        self.original_image = base_image.copy()

        # 4. self.rect を 40x40 で初期化
        self.rect = self.original_image.get_rect(topleft=(x, y))

        # 5. ★★★ 全てのSpikeで共通の当たり判定縮小処理 (4方向) ★★★
        sub_rect = (0, 0, TILE_SIZE, TILE_SIZE)  # デフォルト (念のため)

        if self.orientation == "DOWN":
            # rect を 40x20 (上半分) に縮小
            self.rect.height = TILE_SIZE // 2
            sub_rect = (0, 0, TILE_SIZE, TILE_SIZE // 2)

        elif self.orientation == "UP":
            # rect を 40x20 (下半分) に縮小し、Y座標を下にずらす
            self.rect.height = TILE_SIZE // 2
            self.rect.y += TILE_SIZE // 2
            sub_rect = (0, TILE_SIZE // 2, TILE_SIZE, TILE_SIZE // 2)

        elif self.orientation == "LEFT":
            # rect を 20x40 (左半分) に縮小
            self.rect.width = TILE_SIZE // 2
            sub_rect = (0, 0, TILE_SIZE // 2, TILE_SIZE)

        elif self.orientation == "RIGHT":
            # rect を 20x40 (右半分) に縮小し、X座標を右にずらす
            self.rect.width = TILE_SIZE // 2
            self.rect.x += TILE_SIZE // 2
            sub_rect = (TILE_SIZE // 2, 0, TILE_SIZE // 2, TILE_SIZE)

        # 6. image と mask を、補正後の rect に合わせて更新
        self.image = self.original_image.subsurface(sub_rect)
        self.original_image = self.image.copy()  # original_image も 補正後に更新
        self.mask = pygame.mask.from_surface(self.image)


# ▼▼▼ 修正後の Key クラス ▼▼▼
class Key(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 1. 20x20の透過サーフェスを作成
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # 透過で塗りつぶし

        # 2. 鍵の「輪」を描画 (塗りつぶし)
        pygame.draw.circle(self.image, KEY_COLOR, (10, 6), 5)  # (center, radius)
        # 3. 輪の中を透明で抜く (小さな円)
        pygame.draw.circle(self.image, (0, 0, 0, 0), (10, 6), 2)

        # 4. 鍵の「軸」を描画
        pygame.draw.rect(self.image, KEY_COLOR, (8, 10, 4, 10))  # (x, y, w, h)

        # 5. 鍵の「歯」を描画
        pygame.draw.rect(self.image, KEY_COLOR, (8, 17, 7, 2))

        # 6. rect は変更なし (中央配置)
        self.rect = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))

        # 7. ピクセルパーフェクト判定用のマスクを作成
        self.mask = pygame.mask.from_surface(self.image)


# ▲▲▲ 修正後の Key クラス ここまで ▲▲▲


# ▼▼▼ 修正後の Door クラス ▼▼▼
class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 1. 40x60の透過サーフェスを作成
        self.image = pygame.Surface((40, 60), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # 透過

        # 2. ドア本体 (緑)
        pygame.draw.rect(self.image, DOOR_COLOR, (0, 0, 40, 60), border_radius=4)

        # 3. ドアの枠 (少し暗い緑)
        DOOR_FRAME_COLOR = (0, 120, 0)
        pygame.draw.rect(
            self.image, DOOR_FRAME_COLOR, (0, 0, 40, 60), 3, border_radius=4
        )  # width=3

        # 4. 鍵穴 (カギの色 = 黄色)
        KEYHOLE_COLOR = KEY_COLOR
        # 鍵穴の丸い部分
        pygame.draw.circle(self.image, KEYHOLE_COLOR, (30, 30), 4)
        # 鍵穴の縦棒部分
        pygame.draw.rect(self.image, KEYHOLE_COLOR, (28, 33, 4, 6))

        # 5. rect は変更なし
        self.rect = self.image.get_rect(bottomleft=(x, y + TILE_SIZE))

        # 6. ピクセルパーフェクト判定用のマスクを作成
        self.mask = pygame.mask.from_surface(self.image)


# ▲▲▲ 修正後の Door クラス ここまで ▲▲▲


# --- ステージを構築する関数 ---
def setup_level(level_map):
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    spikes = pygame.sprite.Group()
    keys = pygame.sprite.Group()
    doors = pygame.sprite.Group()
    booster_platforms = pygame.sprite.Group()
    gravity_switchers = pygame.sprite.Group()

    falling_spikes = pygame.sprite.Group()
    patrolling_spikes = pygame.sprite.Group()
    arrow_launchers = pygame.sprite.Group()

    player = None
    start_pos = (0, 0)

    map_height = len(level_map)

    for y, row in enumerate(level_map):
        current_row_len = len(row)
        for x, char in enumerate(row):
            world_x = x * TILE_SIZE
            world_y = y * TILE_SIZE

            # --- Platform/Booster の隣接判定 (P以外の全ての足場キャラを追加) ---
            platform_chars = (
                "P",
                "B",
                "V",
                "Y",
                "C",
                "O",
                "R",
                "L",
                "E",
            )  # 'P' も念のため残す
            has_neighbor_up = (
                y > 0
                and x < len(level_map[y - 1])
                and level_map[y - 1][x] in platform_chars
            )
            has_neighbor_down = (
                y < map_height - 1
                and x < len(level_map[y + 1])
                and level_map[y + 1][x] in platform_chars
            )
            has_neighbor_left = x > 0 and row[x - 1] in platform_chars
            has_neighbor_right = (
                x < current_row_len - 1 and row[x + 1] in platform_chars
            )

            # ★★★ プラットフォームの種類判定ロジックを更新 ★★★
            current_platform = None
            if (
                char == "P"
            ):  # 'P' がマップにあってもエラーにならないよう、Platformクラスを生成
                current_platform = Platform(
                    world_x,
                    world_y,
                    has_neighbor_up,
                    has_neighbor_down,
                    has_neighbor_left,
                    has_neighbor_right,
                )
            elif char == "V":  # 紫色上面のプラットフォーム
                current_platform = PurplePlatform(
                    world_x,
                    world_y,
                    has_neighbor_up,
                    has_neighbor_down,
                    has_neighbor_left,
                    has_neighbor_right,
                )
            elif char == "Y":  # 黄色上面のプラットフォーム
                current_platform = YellowPlatform(
                    world_x,
                    world_y,
                    has_neighbor_up,
                    has_neighbor_down,
                    has_neighbor_left,
                    has_neighbor_right,
                )
            elif char == "C":  # 水色上面のプラットフォーム
                current_platform = CyanPlatform(
                    world_x,
                    world_y,
                    has_neighbor_up,
                    has_neighbor_down,
                    has_neighbor_left,
                    has_neighbor_right,
                )
            elif char == "O":  # オレンジ色上面のプラットフォーム
                current_platform = OrangePlatform(
                    world_x,
                    world_y,
                    has_neighbor_up,
                    has_neighbor_down,
                    has_neighbor_left,
                    has_neighbor_right,
                )
            elif char == "R":  # 赤色上面のプラットフォーム (追加)
                current_platform = RedPlatform(
                    world_x,
                    world_y,
                    has_neighbor_up,
                    has_neighbor_down,
                    has_neighbor_left,
                    has_neighbor_right,
                )
            elif char == "L":  # 青色上面のプラットフォーム (追加)
                current_platform = BluePlatform(
                    world_x,
                    world_y,
                    has_neighbor_up,
                    has_neighbor_down,
                    has_neighbor_left,
                    has_neighbor_right,
                )
            elif char == "E":  # 緑色上面のプラットフォーム (追加)
                current_platform = GreenPlatform(
                    world_x,
                    world_y,
                    has_neighbor_up,
                    has_neighbor_down,
                    has_neighbor_left,
                    has_neighbor_right,
                )
            elif char == "B":  # Booster
                current_platform = BoosterPlatform(
                    world_x,
                    world_y,
                    has_neighbor_up,
                    has_neighbor_down,
                    has_neighbor_left,
                    has_neighbor_right,
                )
                booster_platforms.add(current_platform)  # Boosterグループにも追加

            if current_platform:
                platforms.add(current_platform)
                all_sprites.add(current_platform)
            # ★★★ ここまで ★★★

            elif char == "G":  # GravitySwitcher
                g = GravitySwitcher(world_x, world_y)
                gravity_switchers.add(g)
                all_sprites.add(g)

            # ▼▼▼ 'S', 'F', 'M' の orientation 決定ロジック (ここから) ▼▼▼
            elif char in ("S", "F", "M"):

                # --- 周囲の足場をチェック (P以外の全ての足場キャラを追加) ---
                has_platform_below = (
                    y < map_height - 1
                    and x < len(level_map[y + 1])
                    and level_map[y + 1][x] in platform_chars
                )
                has_platform_above = (
                    y > 0
                    and x < len(level_map[y - 1])
                    and level_map[y - 1][x] in platform_chars
                )
                has_platform_right = (
                    x < current_row_len - 1 and row[x + 1] in platform_chars
                )
                has_platform_left = x > 0 and row[x - 1] in platform_chars

                # --- 向きを決定 (優先順位: ★下 -> 上 -> 右 -> 左★) ---
                orientation = "UP"  # デフォルト

                if has_platform_below:
                    orientation = "UP"
                elif has_platform_above:
                    orientation = "DOWN"
                elif has_platform_right:
                    orientation = "LEFT"  # 右に壁があるので、トゲは左を向く
                elif has_platform_left:
                    orientation = "RIGHT"  # 左に壁があるので、トゲは右を向く

                # --- オブジェクトの生成 ---
                if char == "S":  # Spike
                    s = Spike(world_x, world_y, orientation)
                    spikes.add(s)
                    all_sprites.add(s)

                elif char == "F":  # FallingSpike
                    fs = FallingSpike(world_x, world_y, orientation)
                    spikes.add(fs)
                    falling_spikes.add(fs)
                    all_sprites.add(fs)

                elif char == "M":  # PatrollingSpike
                    ps = PatrollingSpike(world_x, world_y, 80, 2, orientation)
                    spikes.add(ps)
                    patrolling_spikes.add(ps)
                    all_sprites.add(ps)
            # ▲▲▲ 'S', 'F', 'M' のロジックここまで ▲▲▲

            # ▼▼▼ ★★★ 'A' の修正ブロック ★★★ ▼▼▼
            elif char == "A":
                # --- 'A' (ArrowLauncher) の向きを自動判定 ---
                # (プラットフォーム文字は 'S' ブロックの定義と合わせる)
                platform_chars_for_A = ("P", "B", "V", "Y", "C", "O", "R", "L", "E")
                has_platform_right = (
                    x < current_row_len - 1 and row[x + 1] in platform_chars_for_A
                )
                has_platform_left = x > 0 and row[x - 1] in platform_chars_for_A

                direction = 1  # デフォルトは右向き

                if has_platform_right:
                    direction = -1  # 右に壁があれば左向き
                elif has_platform_left:
                    direction = 1  # 左に壁があれば右向き
                # (左右に壁がない場合、x=0 (左端) なら direction = 1 (デフォルト) のままで正しい)

                al = ArrowLauncher(world_x, world_y, direction)
                arrow_launchers.add(al)
                all_sprites.add(al)
            # ▲▲▲ ★★★ 'A' の修正ブロックここまで ★★★ ▲▲▲

            elif char == "K":  # Key
                k = Key(world_x, world_y)
                keys.add(k)
                all_sprites.add(k)
            elif char == "D":  # Door
                d = Door(world_x, world_y)
                doors.add(d)
                all_sprites.add(d)
            elif char == "@":  # Player
                player_x = world_x + (TILE_SIZE - 30) // 2
                player_y = world_y + (TILE_SIZE - 30)
                start_pos = (player_x, player_y)
                player = Player(player_x, player_y)

    if player is None:
        print("エラー: プレイヤー(@)がマップにいません！")
        sys.exit()

    all_sprites.add(player)

    return (
        player,
        start_pos,
        all_sprites,
        platforms,
        spikes,
        keys,
        doors,
        gravity_switchers,
        booster_platforms,
        falling_spikes,
        patrolling_spikes,
        arrow_launchers,
    )


class Arrow(pygame.sprite.Sprite):
    """★ 弓矢（飛んでくる障害物）"""

    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((30, 8))
        self.image.fill(ARROW_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.direction = direction
        self.speed = 5

        # ★ 弓矢にもマスクを追加（トゲと同様の理由）
        self.mask = pygame.mask.from_surface(self.image)

    # ▼▼▼ ★★★ 修正後の update メソッド ★★★ ▼▼▼
    def update(self, *args):  # ★ 引数を *args に変更 (カメラ座標を受け取らない)
        self.rect.x += self.speed * self.direction

        # 画面外での自動消滅ロジックを「削除」
        # これにより、プレイヤーが遠くにいても矢は壁に当たるまで飛び続けます。
        # (壁に当たった時の消滅は main ループの groupcollide で処理されます)

    # ▲▲▲ ★★★ 修正ここまで ★★★ ▲▲▲


class ArrowLauncher(pygame.sprite.Sprite):
    """★ 弓矢の発射台 (自動発射機能付き)"""

    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(LAUNCHER_COLOR)

        if direction == -1:
            self.rect = self.image.get_rect(
                topright=(x + TILE_SIZE, y + (TILE_SIZE // 2) - 10)
            )
        else:
            self.rect = self.image.get_rect(topleft=(x, y + (TILE_SIZE // 2) - 10))

        self.direction = direction
        self.last_spawn_time = pygame.time.get_ticks() + random.randint(0, 500)
        self.spawn_interval = random.randint(MIN_ARROW_INTERVAL, MAX_ARROW_INTERVAL)

    def update(self):
        # この関数はプレイヤーの位置に関係なく、時間だけで発射を決定します。
        now = pygame.time.get_ticks()
        if now - self.last_spawn_time > self.spawn_interval:
            self.last_spawn_time = now
            self.spawn_interval = random.randint(MIN_ARROW_INTERVAL, MAX_ARROW_INTERVAL)

            if self.direction == 1:  # 右向き
                spawn_x = self.rect.right + 1
                spawn_y = self.rect.centery - 4
            else:  # 左向き
                spawn_x = self.rect.left - 31
                spawn_y = self.rect.centery - 4

            return Arrow(spawn_x, spawn_y, self.direction)
        return None


# -----------------------------------------------------------------
# ▼▼▼ FallingSpike クラス全体 (4方向 / 重力反転対応) ▼▼▼
# -----------------------------------------------------------------
class FallingSpike(Spike):
    """プレイヤーが近づくと落ちてくるトゲ"""

    def __init__(self, x, y, orientation="DOWN"):
        # 1. 親クラス(Spike) の init を呼び出し、rect と image を 40x20, 20x40 などに設定
        super().__init__(x, y, orientation)

        # 2. float 座標と start_x/y を、補正後の rect に合わせる
        self.true_x = float(self.rect.x)
        self.true_y = float(self.rect.y)
        self.start_x = self.rect.x
        self.start_y = self.rect.y

        # 3. 物理プロパティを初期化
        self.vel_x = 0
        self.vel_y = 0
        self.is_active = False

    def update(self, platforms, current_gravity):

        if self.is_active:

            # --- 1. 速度更新 (向きと重力に応じる) ---
            self.vel_x = 0  # 基本は X 速度ゼロ

            is_gravity_down = current_gravity == "DOWN"

            # (A) 天井トゲ (orientation == "DOWN")
            if self.orientation == "DOWN":
                if is_gravity_down:
                    # 通常時: 天井トゲは「落ちる」
                    self.vel_y += GRAVITY
                    if self.vel_y > 10:
                        self.vel_y = 10
                else:
                    # 反転時: 天井トゲは「飛ぶ」 (上へ)
                    self.vel_y -= GRAVITY * 1.5
                    if self.vel_y < -10:
                        self.vel_y = -10

            # (B) 床トゲ (orientation == "UP")
            elif self.orientation == "UP":
                if is_gravity_down:
                    # 通常時: 床トゲは「下」に飛ぶ
                    self.vel_y += GRAVITY
                    if self.vel_y > 10:
                        self.vel_y = 10
                else:
                    # 反転時: 床トゲは「上」に落ちる
                    self.vel_y -= GRAVITY * 1.5
                    if self.vel_y < -10:
                        self.vel_y = -10

            # (C) 横向きのトゲ (重力の影響も受ける)
            elif self.orientation == "RIGHT":
                # 「左壁トゲ」は右に飛ぶ
                self.vel_x = 5  # 速度 5 (固定)
                if current_gravity == "DOWN":
                    self.vel_y += GRAVITY
                elif current_gravity == "UP":
                    self.vel_y -= GRAVITY

            elif self.orientation == "LEFT":
                # 「右壁トゲ」は左に飛ぶ
                self.vel_x = -5  # 速度 -5 (固定)
                if current_gravity == "DOWN":
                    self.vel_y += GRAVITY
                elif current_gravity == "UP":
                    self.vel_y -= GRAVITY

            # --- 2. X軸（横）の移動と衝突判定 ---
            if self.vel_x != 0:
                self.true_x += self.vel_x
                self.rect.x = int(self.true_x)

                hit_list_x = pygame.sprite.spritecollide(self, platforms, False)
                if hit_list_x:
                    self.kill()  # 壁に当たったら消える
                    return  # update を終了

            # --- 3. Y軸（縦）の移動と衝突判定 ---
            remaining_y = self.vel_y
            sign = 1 if remaining_y > 0 else -1
            # (Y軸貫通対策)
            max_step_size = self.rect.height - 1
            if max_step_size <= 0:
                max_step_size = 1  # ゼロ除算回避

            while abs(remaining_y) > 0.001:
                step = min(abs(remaining_y), max_step_size) * sign
                self.true_y += step
                self.rect.y = int(self.true_y)

                hit_list_y = pygame.sprite.spritecollide(self, platforms, False)

                if hit_list_y:
                    if current_gravity == "DOWN":
                        if self.vel_y > 0:  # 着地
                            best_platform = min(hit_list_y, key=lambda p: p.rect.top)
                            self.rect.bottom = best_platform.rect.top
                        elif self.vel_y < 0:  # 頭をぶつけた
                            best_platform = max(hit_list_y, key=lambda p: p.rect.bottom)
                            self.rect.top = best_platform.rect.bottom
                    elif current_gravity == "UP":
                        if self.vel_y < 0:  # 着地 (天井へ)
                            best_platform = max(hit_list_y, key=lambda p: p.rect.bottom)
                            self.rect.top = best_platform.rect.bottom
                        elif self.vel_y > 0:  # 頭をぶつけた (床へ)
                            best_platform = min(hit_list_y, key=lambda p: p.rect.top)
                            self.rect.bottom = best_platform.rect.top

                    self.true_y = float(self.rect.y)
                    self.vel_y = 0
                    remaining_y = 0.0

                    self.kill()  # 床/天井に当たっても消える
                    break

                remaining_y -= step

    def activate(self):
        if not self.is_active:  # (vel_y == 0 の条件を削除)
            self.is_active = True

    def reset_position(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.true_x = float(self.start_x)
        self.true_y = float(self.start_y)
        self.vel_x = 0
        self.vel_y = 0
        self.is_active = False
        self.image = self.original_image.copy()
        self.mask = pygame.mask.from_surface(self.image)


# -----------------------------------------------------------------
# ▲▲▲ FallingSpikeクラスここまで ▲▲▲
# -----------------------------------------------------------------


# -----------------------------------------------------------------
# ▼▼▼ PatrollingSpike クラス全体 (★重力削除★) ▼▼▼
# -----------------------------------------------------------------
class PatrollingSpike(Spike):
    """指定された範囲を左右に往復するトゲ (重力なし)"""

    def __init__(self, x, y, move_range, speed, orientation="UP"):
        # 1. 親クラス(Spike) の init を呼び出し、rect と image を 40x20 などに設定
        super().__init__(x, y, orientation)

        # 2. float 座標と original_x/y を、補正後の rect に合わせる
        self.true_x = float(self.rect.x)
        self.true_y = float(self.rect.y)
        self.original_x = self.rect.x  # 補正後の X を保存
        self.original_y = self.rect.y  # 補正後の Y を保存

        # 3. 物理プロパティを初期化
        self.start_x = self.rect.x
        self.end_x = self.rect.x + move_range
        self.vel_x = speed
        self.original_speed = speed
        self.vel_y = 0  # (Y速度は常に0)

    # ★★★ update メソッド ★★★
    def update(self, platforms, current_gravity):

        # 1. X軸（左右）の移動
        self.true_x += self.vel_x
        self.rect.x = int(self.true_x)

        # ★ X軸の移動範囲を補正 (rect.right と rect.left で比較)
        if self.vel_x > 0 and self.rect.right > self.end_x:
            self.rect.right = self.end_x
            self.vel_x = -self.vel_x
        elif self.vel_x < 0 and self.rect.left < self.start_x:
            self.rect.left = self.start_x
            self.vel_x = -self.vel_x
        # X座標を補正した後、true_x も同期する
        self.true_x = float(self.rect.x)

    def reset_position(self):
        self.rect.topleft = (self.original_x, self.original_y)
        self.true_x = float(self.original_x)  # true_x もリセット
        self.true_y = float(self.original_y)  # true_y もリセット
        self.vel_x = self.original_speed
        self.vel_y = 0  # Y軸速度もリセット
        self.image = self.original_image.copy()
        self.mask = pygame.mask.from_surface(self.image)


# -----------------------------------------------------------------
# ▲▲▲ PatrollingSpikeクラス ここまで ▲▲▲
# -----------------------------------------------------------------


# -----------------------------------------------------------------
# ▼▼▼ main 関数 (画面回転を「復活」) ▼▼▼
# -----------------------------------------------------------------
def main():
    gravity_direction = "DOWN"

    pygame.init()

    # ★★★ フォントの初期化 ★★★
    pygame.font.init()
    try:
        font = pygame.font.Font(None, 50)  # デフォルトフォント、サイズ50
    except:
        font = pygame.font.Font(pygame.font.get_default_font(), 50)

    # --- GAME OVER用 テキスト (★ SCREEN サイズ基準に変更) ---
    text_game_over = font.render("GAME OVER", True, WHITE)
    text_retry = font.render("Press Enter to Retry", True, WHITE)
    text_game_over_rect = text_game_over.get_rect(
        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)
    )
    text_retry_rect = text_retry.get_rect(
        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
    )

    # ★★★ クリア画面用のテキスト (★ SCREEN サイズ基準に変更) ★★★
    text_game_clear = font.render("GAME CLEAR!", True, WHITE)
    text_quit = font.render("Press Enter to Quit", True, WHITE)
    text_game_clear_rect = text_game_clear.get_rect(
        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)
    )
    text_quit_rect = text_quit.get_rect(
        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
    )
    # ★★★ ここまで ★★★

    # ★★★ 暗転用サーフェスの作成 (★ SCREEN サイズ基準に変更) ★★★
    dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dark_overlay.fill((0, 0, 0, 150))  # 黒色で、透明度150 (0-255)
    # ★★★ ここまで ★★★

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    pygame.display.set_caption("Minimalism Prototype (Expanded)")
    clock = pygame.time.Clock()

    (
        player,
        start_pos,
        all_sprites,
        platforms,
        spikes,
        keys,
        doors,
        gravity_switchers,
        booster_platforms,
        falling_spikes,
        patrolling_spikes,
        arrow_launchers,
    ) = setup_level(LEVEL_MAP)

    arrows = pygame.sprite.Group()

    if len(LEVEL_MAP) > 0:
        level_width = max(len(row) for row in LEVEL_MAP) * TILE_SIZE
    else:
        level_width = GAME_WIDTH
    level_height = len(LEVEL_MAP) * TILE_SIZE

    camera_x = 0
    camera_y = 0

    game_state = "PLAYING"  # ★ ステート管理

    # ★★★ アニメーション関連の変数を復活 ★★★
    animation_timer = 0.0  # アニメーションの進捗 (0.0 -> 1.0)
    ANIMATION_DURATION_SECONDS = 0.5  # アニメーションの所要時間 (秒)

    # target_gravity はアニメーション後の重力方向
    target_gravity = "DOWN"

    # 現在の画面の回転角度 (0.0 or 180.0)
    current_angle = 0.0
    # アニメーション中の目標角度
    target_angle = 0.0
    # ★★★ ここまで ★★★

    # --- ★ 星空の背景を生成 ★ ---
    stars = []
    for _ in range(NUM_STARS):
        # 星をレベル全体の範囲、あるいはそれより少し広めに配置する
        # (Parallaxで端が見えないように、-GAME_WIDTH/2 から level_width + GAME_WIDTH/2 まで)
        x = random.randint(-GAME_WIDTH // 2, level_width + GAME_WIDTH // 2)
        y = random.randint(-GAME_HEIGHT // 2, level_height + GAME_HEIGHT // 2)
        radius = random.randint(1, 2)
        color = random.choice(STAR_COLORS)
        stars.append((x, y, radius, color))
    # --- ★ ここまで ★ ---

    while True:
        # --- イベント処理 (共通) ---
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # ▼▼▼ PLAYING 中のみ反応するキー入力 ▼▼▼
            if game_state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    if (
                        event.key == pygame.K_SPACE
                        or event.key == pygame.K_UP
                        or event.key == pygame.K_w
                    ):
                        player.jump(gravity_direction)

                if event.type == pygame.KEYUP:
                    if (
                        event.key == pygame.K_SPACE
                        or event.key == pygame.K_UP
                        or event.key == pygame.K_w
                    ):
                        player.cut_jump(
                            gravity_direction
                        )  # 引数に gravity_direction を渡す
            # ▲▲▲ PLAYING 中のキー入力ここまで ▲▲▲

        # --- 更新処理 ---
        if game_state == "PLAYING":

            # 弓矢の発射
            for launcher in arrow_launchers:
                new_arrow = launcher.update()
                if new_arrow:
                    all_sprites.add(new_arrow)
                    arrows.add(new_arrow)

            # ▼▼▼ ★★★ 修正箇所 ★★★ ▼▼▼
            arrows.update()  # ★ 引数を削除 (カメラ座標を渡さない)
            # ▲▲▲ ★★★ 修正ここまで ★★★ ▲▲▲

            pygame.sprite.groupcollide(arrows, platforms, True, False)  # 矢と壁の衝突

            # ★★★ FallingSpike の起動ロジック (4方向対応) ★★★
            for fs in falling_spikes:

                if fs.orientation == "DOWN":
                    # プレイヤーが「下」にいる
                    if (
                        not fs.is_active
                        and abs(player.rect.centerx - fs.rect.centerx) < 50  # X軸が近い
                        and player.rect.top > fs.rect.bottom  # Y軸が下
                        and (player.rect.top - fs.rect.bottom) < 200
                    ):  # 200px以内
                        fs.activate()

                elif fs.orientation == "UP":
                    # プレイヤーが「上」にいる
                    if (
                        not fs.is_active
                        and abs(player.rect.centerx - fs.rect.centerx) < 50  # X軸が近い
                        and player.rect.bottom < fs.rect.top  # Y軸が上
                        and (fs.rect.top - player.rect.bottom) < 200
                    ):  # 200px以内
                        fs.activate()

                elif fs.orientation == "LEFT":
                    # プレイヤーが「左」にいる
                    if (
                        not fs.is_active
                        and abs(player.rect.centery - fs.rect.centery) < 50  # Y軸が近い
                        and player.rect.right < fs.rect.left  # X軸が左
                        and (fs.rect.left - player.rect.right) < 200
                    ):  # 200px以内
                        fs.activate()

                elif fs.orientation == "RIGHT":
                    # プレイヤーが「右」にいる
                    if (
                        not fs.is_active
                        and abs(player.rect.centery - fs.rect.centery) < 50  # Y軸が近い
                        and player.rect.left > fs.rect.right  # X軸が右
                        and (player.rect.left - fs.rect.right) < 200
                    ):  # 200px以内
                        fs.activate()

            # ★★★ 足場 (platforms) の update を呼び出す ★★★
            platforms.update(
                gravity_direction
            )  # (booster_platforms も platforms に含まれる)

            # 各グループの更新
            falling_spikes.update(platforms, gravity_direction)
            patrolling_spikes.update(platforms, gravity_direction)

            player.update(platforms, gravity_direction)

            # 落下ミス判定 (★ GAME_OVER に変更)
            if (
                player.rect.top > level_height
                or player.rect.bottom < 0
                or (
                    level_width > 0
                    and (player.rect.left > level_width or player.rect.right < 0)
                )
            ):

                print("落下ミス！")
                game_state = "GAME_OVER"

            # ブースター判定
            is_on_booster = (
                any(isinstance(p, BoosterPlatform) for p in player.standing_on)
                if player.on_ground
                else False
            )
            player.speed_multiplier = 2.0 if is_on_booster else 1.0
            player.jump_multiplier = (
                2.0 if is_on_booster else 1.0
            )  # ブーストジャンプ調整

            # ★★★ 重力スイッチ判定 (アニメーションへ移行) ★★★
            collided_switcher = pygame.sprite.spritecollideany(
                player, gravity_switchers
            )
            if collided_switcher:

                # 現在の重力に基づいて、目標の重力と角度を設定
                if gravity_direction == "DOWN":
                    target_gravity = "UP"
                    target_angle = 180.0
                else:
                    target_gravity = "DOWN"
                    target_angle = 0.0

                game_state = "ANIMATING"  # ステートをアニメーションに変更
                animation_timer = 0.0  # アニメーションタイマーをリセット
                print(f"アニメーション開始！ ターゲット: {target_gravity}")
                collided_switcher.kill()

            # カメラの更新 (プレイヤー中央)
            target_camera_x = player.rect.centerx - GAME_WIDTH // 2
            target_camera_y = player.rect.centery - GAME_HEIGHT // 2

            # カメラの範囲をレベルの範囲に制限
            if level_width > GAME_WIDTH:
                camera_x = max(0, min(target_camera_x, level_width - GAME_WIDTH))
            else:
                camera_x = (level_width - GAME_WIDTH) // 2

            if level_height > GAME_HEIGHT:
                camera_y = max(0, min(target_camera_y, level_height - GAME_HEIGHT))
            else:
                camera_y = (level_height - GAME_HEIGHT) // 2

            # 弓矢との衝突 (Mask判定) (★ GAME_OVER に変更)
            if pygame.sprite.spritecollide(
                player, arrows, True, pygame.sprite.collide_mask
            ):
                print("矢に当たった！")
                game_state = "GAME_OVER"

            # トゲとの衝突 (Mask判定) (★ GAME_OVER に変更)
            elif pygame.sprite.spritecollide(
                player, spikes, False, pygame.sprite.collide_mask
            ):
                print("ミス！")
                game_state = "GAME_OVER"

            # カギ・トビラ判定
            # ★ カギの衝突判定を collide_mask に変更 ★
            if pygame.sprite.spritecollide(
                player, keys, True, pygame.sprite.collide_mask
            ):
                player.has_key = True
                print("カギを手に入れた！")

            # GAME_CLEAR ステートへ
            # ★ トビラの衝突判定を collide_mask に変更 ★
            if (
                pygame.sprite.spritecollide(
                    player, doors, False, pygame.sprite.collide_mask
                )
                and player.has_key
            ):
                print("クリア！おめでとう！")
                game_state = "GAME_CLEAR"  # 終了する代わりにステートを変更

        # ★★★ GAME_OVER ステートの処理 ★★★
        elif game_state == "GAME_OVER":
            # Enterキーが押されるまで待機
            for event in events:  # 共通イベントキューをチェック
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:

                        # --- リセット処理 (ここですべて行う) ---
                        print("リスタートします。")
                        all_sprites.empty()
                        platforms.empty()
                        spikes.empty()
                        keys.empty()
                        doors.empty()
                        gravity_switchers.empty()
                        booster_platforms.empty()
                        falling_spikes.empty()
                        patrolling_spikes.empty()
                        arrow_launchers.empty()
                        arrows.empty()

                        (
                            player,
                            start_pos,
                            all_sprites,
                            platforms,
                            spikes,
                            keys,
                            doors,
                            gravity_switchers,
                            booster_platforms,
                            falling_spikes,
                            patrolling_spikes,
                            arrow_launchers,
                        ) = setup_level(LEVEL_MAP)

                        player.reset_position(*start_pos)
                        gravity_direction = "DOWN"  # ★リセット時は必ずDOWNに戻す

                        # ★ アニメーション関連のリセット (追加) ★
                        current_angle = 0.0
                        target_angle = 0.0
                        animation_timer = 0.0
                        target_gravity = "DOWN"

                        game_state = "PLAYING"

                        break  # リセットしたらこのフレームの処理は終了
        # ★★★ GAME_OVER 処理ここまで ★★★

        # ★★★ GAME_CLEAR ステートの処理 ★★★
        elif game_state == "GAME_CLEAR":
            # Enterキーが押されるまで待機
            for event in events:  # 共通イベントキューをチェック
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        print("ゲームを終了します。")
                        pygame.quit()
                        sys.exit()
        # ★★★ GAME_CLEAR 処理ここまで ★★★

        # ★★★ ANIMATING ステートの処理 (復活) ★★★
        elif game_state == "ANIMATING":
            # 1. 時間を経過させる (clock.tick() から秒数を計算)
            delta_time_seconds = clock.get_time() / 1000.0

            # アニメーション時間が 0 の場合でもゼロ除算にならないように
            if ANIMATION_DURATION_SECONDS > 0:
                animation_timer += delta_time_seconds / ANIMATION_DURATION_SECONDS
            else:
                animation_timer = 1.0  # 即座に終了

            # 2. 現在の角度を計算 (線形補間)
            # 現在の角度 (アニメ開始時の角度)
            current_angle_start = 180.0 if gravity_direction == "UP" else 0.0

            # 補間
            # 例: 0 -> 180 (timer=0.2): 0 + (180 - 0) * 0.2 = 36
            # 例: 180 -> 0 (timer=0.2): 180 + (0 - 180) * 0.2 = 180 - 36 = 144
            current_angle = (
                current_angle_start
                + (target_angle - current_angle_start) * animation_timer
            )

            # 3. アニメーションが終了したか？
            if animation_timer >= 1.0:
                current_angle = target_angle  # 角度をターゲットに固定
                gravity_direction = target_gravity  # 重力を本適用
                game_state = "PLAYING"  # ステートを戻す
                print(f"アニメーション終了。 重力: {gravity_direction}")

            # ★ アニメーション中もカメラはプレイヤーを追従する
            target_camera_x = player.rect.centerx - GAME_WIDTH // 2
            target_camera_y = player.rect.centery - GAME_HEIGHT // 2

            if level_width > GAME_WIDTH:
                camera_x = max(0, min(target_camera_x, level_width - GAME_WIDTH))
            else:
                camera_x = (level_width - GAME_WIDTH) // 2

            if level_height > GAME_HEIGHT:
                camera_y = max(0, min(target_camera_y, level_height - GAME_HEIGHT))
            else:
                camera_y = (level_height - GAME_HEIGHT) // 2
        # ★★★ ANIMATING 処理ここまで ★★★

        # --- 描画処理 ---
        game_surface.fill(GAME_BACKGROUND_COLOR)  # ★背景色を (暗い紺色) に変更

        # --- ★ 星空の描画 (Parallax効果) ★ ---
        for x, y, radius, color in stars:
            # 星のワールド座標 (x, y) からカメラ座標を引く
            # Parallaxをかけるため、カメラ座標に係数をかける
            screen_x = x - (camera_x * PARALLAX_FACTOR)
            screen_y = y - (camera_y * PARALLAX_FACTOR)

            # 画面外の星は描画しない (簡易的なカリング)
            if 0 <= screen_x <= GAME_WIDTH and 0 <= screen_y <= GAME_HEIGHT:
                pygame.draw.circle(
                    game_surface, color, (int(screen_x), int(screen_y)), radius
                )
        # --- ★ ここまで ★ ---

        # スプライトの描画
        for sprite in all_sprites:
            screen_x = sprite.rect.x - camera_x
            screen_y = sprite.rect.y - camera_y
            game_surface.blit(sprite.image, (screen_x, screen_y))

        # ★★★ 画面の回転・拡縮ロジックを (回転を復活) ★★★

        # 1. game_surface を SCREEN サイズに拡大
        base_display_surface = pygame.transform.scale(
            game_surface, (SCREEN_WIDTH, SCREEN_HEIGHT)
        )

        # 2. ウィンドウの余白を埋める
        screen.fill(WHITE)

        # 3. 拡大したゲーム画面を (current_angle) だけ回転させて描画
        if current_angle == 0:
            # 0度の時は transform.rotate を呼ばない (効率化)
            screen.blit(base_display_surface, (0, 0))
        else:
            # current_angle に応じて回転
            rotated_surface = pygame.transform.rotate(
                base_display_surface, current_angle
            )
            rotated_rect = rotated_surface.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            )
            screen.blit(rotated_surface, rotated_rect)

        # ★★★ UIの描画 (回転・拡縮の影響を受けないよう、screen に直接描画) ★★★
        if game_state == "GAME_OVER":
            screen.blit(dark_overlay, (0, 0))  # 暗転レイヤーを重ねる
            screen.blit(text_game_over, text_game_over_rect)
            screen.blit(text_retry, text_retry_rect)

        elif game_state == "GAME_CLEAR":
            screen.blit(dark_overlay, (0, 0))  # 暗転レイヤーを重ねる
            screen.blit(text_game_clear, text_game_clear_rect)
            screen.blit(text_quit, text_quit_rect)
        # ★★★ 描画ここまで ★★★

        pygame.display.flip()
        clock.tick(FPS)


# -----------------------------------------------------------------
# ▲▲▲ main 関数 ここまで ▲▲▲
# -----------------------------------------------------------------


if __name__ == "__main__":
    main()
