import mido
import pygame
import sys
import random
import os
import cv2
import mediapipe as mp

# ゲーム設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
LANE_WIDTH = SCREEN_WIDTH // 8
NOTE_WIDTH = 80  # ノーツの幅（横長に変更）
NOTE_HEIGHT = 20  # ノーツの高さ（縦長に変更）
LANE_COUNT = 8
BEAM_THICKNESS = 12  # 横線の太さを2倍に変更
LANE_LINE_THICKNESS = 2  # レーンの分割線の太さ
LANE_LINE_COLOR = (255, 255, 255)  # レーンの分割線の色
NOTE_COLOR = (0, 191, 255)  # ノーツの色（水色）
FLICK_COLOR=(255,67,133)#フリック色(ピンク色)
LINE_COLOR = (255, 255, 255)  # 横線の色
LINE_Y_POSITION = SCREEN_HEIGHT - 100  # 横線の位置
CATCH_RADIUS = 50  # ノーツをキャッチできる範囲
GLOW_COLOR = (0, 255, 0)  # 輝く色（緑色）
GLOW_DURATION = 250  # 輝く持続時間（ミリ秒）
RESULT_FONT_SIZE = 72
RESULT_FONT_COLOR = (255, 255, 0)
pygame.mixer.init()
SOUND_EFFECT1 = pygame.mixer.Sound("./Sound effect/sound_effect1.mp3")#選択するときの音
SOUND_EFFECT2 = pygame.mixer.Sound("./Sound effect/sound_effect2.mp3")#決定するときの音
NOTE_EFFECT = pygame.mixer.Sound("./Sound effect/note_effect.mp3")
FLICK_EFFECT = pygame.mixer.Sound("./Sound effect/flick_effect.mp3")
# 難易度の設定
DIFFICULTY_LEVELS = {
    'easy': 0.3,
    'normal': 0.5,
    'hard': 1.0
}

# フォントの設定
MENU_FONT = None
MENU_FONT_SIZE = 36
SELECTION_COLOR = (255, 255, 0)
UNSELECTED_COLOR = (150, 150, 150)
COMBO_FONT_SIZE = 48
COMBO_FONT_COLOR = (255, 255, 255)
BG_COLOR = (0, 0, 0)
MAX_VISIBLE_FILES = 6
font_path = "./Zen_Antique_Soft/ZenAntiqueSoft-Regular.ttf"
pygame.font.init()
font_size = 24
analog_font = pygame.font.Font(font_path, font_size)

#曲の終わる時間
def midi_finish(file_path):
    midi_file=mido.MidiFile(file_path)
    total_time=sum(msg.time for msg in midi_file if not msg.is_meta)
    return total_time

# MIDIファイルの読み込みと解析
def load_midi(file, difficulty='hard'):
    mid = mido.MidiFile(file)
    notes = []

    for track in mid.tracks:
        absolute_time = 0
        for msg in track:
            if not msg.is_meta:
                absolute_time += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    # 時間を1秒（1000ミリ秒）に丸める
                    rounded_time = ((absolute_time + 500) // 1000) * 1000
                
                    # 同じ時間かつ msg.note % 8 の値が同じ場合のみ削除する
                    filtered_notes = [(n, t) for n, t in notes if not (t == rounded_time and n % 8 == msg.note % 8)]
                    notes = filtered_notes
                
                    # 新しいノートを追加
                    notes.append((msg.note, rounded_time))

        
    
    game_notes = []
    tempo = 500000  # デフォルトのテンポ（マイクロ秒/beat）
    ticks_per_beat = mid.ticks_per_beat
    lim=0
    for note, time in notes:
        time_ms = mido.tick2second(time, ticks_per_beat, tempo) * 1000
        if lim%5!=0:
            game_notes.append({'note': note, 'time': time_ms})
        lim=lim+1

    # ノーツの数を難易度に応じて減らす
    random.shuffle(game_notes)
    num_notes = int(len(game_notes) * DIFFICULTY_LEVELS[difficulty])
    game_notes = game_notes[:num_notes]

    return game_notes

def load_midi2(file, difficulty='hard'):
    mid = mido.MidiFile(file)
    notes = []
    for i, track in enumerate(mid.tracks):
        absolute_time = 0
        for msg in track:
            if not msg.is_meta:
                absolute_time += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    rounded_time = ((absolute_time + 500) // 1000) * 1000
                
                    # 同じ時間かつ msg.note % 8 の値が同じ場合のみ削除する
                    filtered_notes = [(n, t) for n, t in notes if not (t == rounded_time)]
                    notes = filtered_notes
                    notes.append((msg.note, rounded_time))
    
    flick_notes = []
    tempo = 500000  # デフォルトのテンポ（マイクロ秒/beat）
    ticks_per_beat = mid.ticks_per_beat
    lim=0
    for note, time in notes:
        time_ms = mido.tick2second(time, ticks_per_beat, tempo) * 1000
        if lim%5==0:
            flick_notes.append({'note': note, 'time': time_ms})
        lim=lim+1

    # ノーツの数を難易度に応じて減らす
    random.shuffle(flick_notes)
    num_notes = int(len(flick_notes) * DIFFICULTY_LEVELS[difficulty])
    flick_notes = flick_notes[:num_notes]

    return flick_notes



    # ノーツの数を難易度に応じて減らす
    random.shuffle(game_notes)
    num_notes = int(len(game_notes) * DIFFICULTY_LEVELS[difficulty])
    game_notes = game_notes[:num_notes]

    return game_notes

# ゲームの初期化
def init_game():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    return screen

# ディレクトリからMIDIファイルのリストを取得する関数
def get_midi_files(directory):
    return [f for f in os.listdir(directory) if f.endswith('.mid')]

# 曲選択画面を表示する関数
def show_song_selection_menu(screen, midi_files):
    global MENU_FONT
    if not MENU_FONT:
        MENU_FONT = pygame.font.Font(None, MENU_FONT_SIZE)

    selected_index = 0
    scroll_offset = 0

    while True:
        background_img = pygame.image.load('./image/background.png').convert()
        background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(background_img, (0, 0))
        visible_files = midi_files[scroll_offset:scroll_offset + MAX_VISIBLE_FILES]

        for idx, midi_file in enumerate(visible_files):
            actual_index = idx + scroll_offset
            text_color = SELECTION_COLOR if actual_index == selected_index else UNSELECTED_COLOR
            midi_text = analog_font.render(midi_file, True, text_color)
            midi_rect = midi_text.get_rect(midleft=(170, 180 + idx * 50))
            screen.blit(midi_text, midi_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    SOUND_EFFECT1.play()
                    if selected_index > 0:
                        selected_index = (selected_index - 1) % len(midi_files)
                        if selected_index < scroll_offset:
                            scroll_offset = selected_index
                    full_path = os.path.join('.\music', midi_files[selected_index])
                    pygame.mixer.music.load(full_path)
                    pygame.mixer.music.play()
                elif event.key == pygame.K_DOWN:
                    SOUND_EFFECT1.play()
                    if selected_index < len(midi_files) - 1:
                        selected_index = (selected_index + 1) % len(midi_files)
                        if selected_index >= scroll_offset + MAX_VISIBLE_FILES:
                            scroll_offset = selected_index - MAX_VISIBLE_FILES + 1
                    full_path = os.path.join('.\music', midi_files[selected_index])
                    pygame.mixer.music.load(full_path)
                    pygame.mixer.music.play()
                elif event.key == pygame.K_RETURN:
                    SOUND_EFFECT2.play()
                    return midi_files[selected_index]
# 難易度選択画面を表示する関数
def show_difficulty_selection_menu(screen):
    options = ['1. Easy', '2. Normal', '3. Hard']
    selected_difficulty = None
    selected_index = 0

    # Load and scale background image
    background_img = pygame.image.load('./image/background.png').convert()
    background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
  
    while True:
        # Draw the background image first
        screen.blit(background_img, (0, 0))

        for idx, option in enumerate(options):
            text_color = SELECTION_COLOR if idx == selected_index else UNSELECTED_COLOR
            option_text = analog_font.render(option, True, text_color)
            option_rect = option_text.get_rect(midleft=(180, 220 + idx * 50))
            screen.blit(option_text, option_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    SOUND_EFFECT1.play()
                    selected_index = (selected_index - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    SOUND_EFFECT1.play()
                    selected_index = (selected_index + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    SOUND_EFFECT2.play()
                    selected_difficulty = options[selected_index].split('.')[1].strip().lower()
                    return selected_difficulty

# ゲームのメインループ
def main_loop(screen, game_notes,flick_notes, midi_file):
    finish_time=midi_finish(midi_file)
    perfect_notes = 0   #perfectの計算
    missed_notes = 0    #missの計算
    clock = pygame.time.Clock()
    cap = cv2.VideoCapture(0) # カメラの初期化
    pygame.time.delay(5000)
    pygame.mixer.music.load(midi_file)
    pygame.mixer.music.play()
    running = True
    start_time = pygame.time.get_ticks()
    total_notes = len(game_notes)+len(flick_notes)-1
    lane_lines = [(i * LANE_WIDTH, 0, i * LANE_WIDTH, SCREEN_HEIGHT) for i in range(1, LANE_COUNT)]
    lane_states = [0] * LANE_COUNT  # 各レーンの状態（0: 通常, >0: 輝いている）
    lane_states2=[0]*LANE_COUNT
    glow_states = [0] * 6  # 6つの横線セグメントの状態（0: 通常, >0: 輝いている）
    mp_hands = mp.solutions.hands# MediaPipeの初期化
    hands = mp_hands.Hands()
    combo_count = 0
    combo_font = pygame.font.Font(None, COMBO_FONT_SIZE)
    combo_text_position = (SCREEN_WIDTH - 200, 20)
    keys = [pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k, pygame.K_l]
    game_notes = [note for note in game_notes if note['time'] not in {flick_note['time'] for flick_note in flick_notes}]
    while running:
        background_img = pygame.image.load('./image/game_background.jpg').convert()
        background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(background_img, (0, 0))
        current_time = pygame.time.get_ticks() - start_time-3000
        if 50>current_time and current_time>0:
                pygame.mixer.music.load(midi_file)
                pygame.mixer.music.play()        
        for i in range(6):
            if catch_note_in_out(screen, game_notes, i+1, current_time-200):
             missed_notes+=1
             combo_count=0
             lane_states2[i] = current_time

        for i in range(6):
            if catch_note_in_out(screen, flick_notes, i+1, current_time-200):
             missed_notes+=1
             combo_count=0
             lane_states2[i] = current_time
        
        ret, frame = cap.read()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)
        if result.multi_hand_landmarks:
            display_value = 1
        else:
            display_value = 0

        if display_value==1:
            for i in range(6):
                for note in flick_notes[:]:
                    note_time = note['time']
                    if current_time <= note_time < current_time + 2000:
                        y_pos = 600 - (600 * (note_time - current_time) / 2000)
                        if abs(y_pos - LINE_Y_POSITION) <= CATCH_RADIUS:
                            if note['note'] % LANE_COUNT == i:
                                flick_notes.remove(note)
                                combo_count += 1
                                perfect_notes += 1
                                FLICK_EFFECT.play()
                                lane_states[i] = current_time
                for note in flick_notes[:]:
                    note_time = note['time']
                    if current_time+200 <= note_time < current_time + 2200:
                        y_pos = 600 - (600 * (note_time - current_time+200) / 2000)
                        if abs(y_pos - LINE_Y_POSITION) <= CATCH_RADIUS:
                            if note['note'] % LANE_COUNT == i:
                                flick_notes.remove(note)
                                combo_count = 0
                                missed_notes += 1
                                lane_states2[i] = current_time+200
                for note in flick_notes[:]:
                    note_time = note['time']
                    if current_time-200 <= note_time < current_time + 1800:
                        y_pos = 600 - (600 * (note_time - current_time-200) / 2000)
                        if abs(y_pos - LINE_Y_POSITION) <= CATCH_RADIUS:
                            if note['note'] % LANE_COUNT == i:
                                flick_notes.remove(note)
                                combo_count = 0
                                missed_notes += 1
                                lane_states2[i] = current_time-200

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in keys:
                    lane_index = keys.index(event.key)
                    glow_states[lane_index] = current_time
                    if catch_note_in_lane(screen, game_notes, lane_index + 1, current_time):
                        combo_count += 1
                        perfect_notes += 1
                        lane_states[lane_index] = current_time
                        NOTE_EFFECT.play()
                    elif catch_note_in_lane(screen, game_notes, lane_index + 1, current_time + 200) or catch_note_in_lane(screen, game_notes, lane_index + 1, current_time - 200):
                        combo_count = 0
                        missed_notes += 1
                        lane_states2[lane_index] = current_time
        # 描画
        ##screen.fill((0, 0, 0))

        # レーンの分割線を描画
        for line in lane_lines:
            pygame.draw.line(screen, LANE_LINE_COLOR, line[:2], line[2:], LANE_LINE_THICKNESS)

        # 横線とその上のコンボ数を描画
        for i in range(6):
            if glow_states[i] > 0:
                pygame.draw.line(screen, GLOW_COLOR, ((i + 1) * LANE_WIDTH, LINE_Y_POSITION),
                                 ((i + 2) * LANE_WIDTH, LINE_Y_POSITION), BEAM_THICKNESS)
                if current_time - glow_states[i] > GLOW_DURATION:
                    glow_states[i] = 0
            else:
                pygame.draw.line(screen, LINE_COLOR, ((i + 1) * LANE_WIDTH, LINE_Y_POSITION),
                                 ((i + 2) * LANE_WIDTH, LINE_Y_POSITION), BEAM_THICKNESS)

             # レーン上に"PERFECT"を表示
            if lane_states[i] > 0:
                 perfect_text = combo_font.render('PERFECT', True, GLOW_COLOR)
                 perfect_rect = perfect_text.get_rect(center=((i + 1.5) * LANE_WIDTH, LINE_Y_POSITION-15))
                 screen.blit(perfect_text, perfect_rect)
                 if current_time - lane_states[i] > GLOW_DURATION:
                     lane_states[i] = 0
            if lane_states2[i] > 0:
                 perfect_text = combo_font.render('MISS', True, (255,0,0))
                 perfect_rect = perfect_text.get_rect(center=((i + 1.5) * LANE_WIDTH, LINE_Y_POSITION-15))
                 screen.blit(perfect_text, perfect_rect)
                 if current_time - lane_states2[i] > GLOW_DURATION:
                    lane_states2[i] = 0

        # ノーツを描画
        for note in game_notes[:]:
            note_time = note['time']
            if current_time > note_time + 2000:
                game_notes.remove(note)
            elif current_time <= note_time < current_time + 2000:
                lane_index = note['note'] % LANE_COUNT
                if 1 <= lane_index <= 6:
                    lane_start_x = lane_index * LANE_WIDTH
                    y_pos = 600 - (600 * (note_time - current_time)*1.5 / 2000)
                    note_rect = pygame.Rect(int(lane_start_x + (LANE_WIDTH - NOTE_WIDTH) / 2),
                                            int(y_pos - NOTE_HEIGHT / 2), NOTE_WIDTH, NOTE_HEIGHT)
                    pygame.draw.rect(screen, NOTE_COLOR, note_rect)
        
        for note2 in flick_notes[:]:
            note_time = note2['time']
            if current_time > note_time + 2000:
                flick_notes.remove(note2)
            elif current_time <= note_time < current_time + 2000:
                lane_index = note2['note'] % LANE_COUNT
                if 1 <= lane_index <= 6:
                    lane_start_x = lane_index * LANE_WIDTH
                    y_pos = 600 - (600 * (note_time - current_time)*1.5 / 2000)

                    # 三角形の頂点を計算
                    top_point = (int(lane_start_x + LANE_WIDTH / 2), int(y_pos - NOTE_HEIGHT / 2))
                    left_point = (int(lane_start_x + (LANE_WIDTH - NOTE_WIDTH) / 2), int(y_pos + NOTE_HEIGHT / 2))
                    right_point = (int(lane_start_x + (LANE_WIDTH + NOTE_WIDTH) / 2), int(y_pos + NOTE_HEIGHT / 2))

                    # 三角形を描画
                    pygame.draw.polygon(screen, FLICK_COLOR, [top_point, left_point, right_point])



        # コンボ数を描画
        combo_text = combo_font.render(f'Combo: {combo_count}', True, COMBO_FONT_COLOR)
        screen.blit(combo_text, combo_text_position)
        if finish_time<current_time/1020:
            running=False
        pygame.display.flip()
        clock.tick(60)

    pygame.mixer.music.stop()
    show_results_screen(screen, total_notes, perfect_notes, missed_notes)
    # 結果画面を一定時間表示
    pygame.time.wait(5000)

def catch_note_in_out(screen, game_notes, lane_index, current_time):
    for note in game_notes[:]:
        note_time = note['time']
        #if note_time < current_time:
        y_pos = 600 - (600 * (note_time - current_time) / 2000)
        if y_pos - LINE_Y_POSITION > CATCH_RADIUS:
            if note['note'] % LANE_COUNT == lane_index:
                    game_notes.remove(note)
                    return True
    return False

def catch_note_in_lane(screen, game_notes, lane_index, current_time):
    for note in game_notes[:]:
        note_time = note['time']
        if current_time <= note_time < current_time + 2000:
            y_pos = 600 - (600 * (note_time - current_time) / 2000)
            if abs(y_pos - LINE_Y_POSITION) <= CATCH_RADIUS:
                if note['note'] % LANE_COUNT == lane_index:
                    game_notes.remove(note)
                    return True
    return False

def show_results_screen(screen, total_notes, perfect_notes, missed_notes):
    global MENU_FONT
    if not MENU_FONT:
        MENU_FONT = pygame.font.Font(None, RESULT_FONT_SIZE)

    screen.fill((0, 0, 0))

    if total_notes > 0:
        perfect_percentage = (perfect_notes / total_notes) * 100
    else:
        perfect_percentage = 0

    result_text = MENU_FONT.render(f"Perfect Notes: {perfect_notes}", True, RESULT_FONT_COLOR)
    percentage_text = MENU_FONT.render(f"Perfect Percentage: {perfect_percentage:.2f}%", True, RESULT_FONT_COLOR)
    missed_text = MENU_FONT.render(f"Missed Notes: {missed_notes}", True, RESULT_FONT_COLOR)

    screen.blit(result_text, (200, 200))
    screen.blit(percentage_text, (200, 300))
    screen.blit(missed_text, (200, 400))

    pygame.display.flip()
if __name__ == '__main__':
    pygame.mixer.pre_init(44100, -16, 2, 512)  # オーディオ初期化
    midi_directory = r'./music/'  # MIDIファイルが保存されているディレクトリ
    midi_files = get_midi_files(midi_directory)
    
    screen = init_game()
    
    # 曲選択画面
    midi_file = show_song_selection_menu(screen, midi_files)
    full_path = os.path.join(midi_directory, midi_file)
    
    # 難易度選択画面
    difficulty = show_difficulty_selection_menu(screen)
    
    # MIDIファイルの読み込みとゲームの初期化
    game_notes = load_midi(full_path, difficulty)
    flick_notes=load_midi2(full_path,difficulty)
    
    # ゲームのメインループ
    main_loop(screen, game_notes, flick_notes,full_path)