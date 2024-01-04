import librosa
import librosa.display
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import os
import librosa.display
import numpy as np
import aubio

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # program root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

# 读取音 频文件
audio_file = ROOT / "audio/song_demo.mp3"  # 替换为你的音频文件路径
audio_file_1 = ROOT / "audio/qilai/qilai.wav"
audio_file_2 = ROOT / "audio/qilai/qilai_1.wav"

'''对音频格式的文件使用Matplotlib库来绘制常见的五种音频图'''


def formGraph(audio_file):
    y, sr = librosa.load(audio_file)

    # 计算onset envelope
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)

    # 使用tempo和beat_frames识别节拍
    tempo, beat_frames = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

    # 绘制音频波形和节拍
    plt.figure(figsize=(20, 15))

    # 音频波形
    plt.subplot(4, 3, 1)
    librosa.display.waveshow(y, sr=sr, alpha=0.5)
    plt.vlines(librosa.frames_to_time(beat_frames), -1, 1, color='r', linestyle='--', label='Beats')
    plt.title(f'Beat Detection at {tempo:.2f} BPM')
    plt.legend()

    # 绘制谱图
    plt.subplot(4, 3, 2)
    spectrogram = librosa.stft(y)
    spectrogram_db = librosa.amplitude_to_db(np.abs(spectrogram))
    librosa.display.specshow(spectrogram_db, sr=sr, x_axis='time', y_axis='log')
    plt.colorbar(format='%+2.0f dB')

    # 梅尔频谱图
    plt.subplot(4, 3, 4)
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_dB = librosa.power_to_db(S, ref=np.max)
    librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel')
    plt.title('Mel Spectrogram')

    # 频率-时间图
    plt.subplot(4, 3, 5)
    plt.specgram(y, NFFT=2048, Fs=2, Fc=0, noverlap=128, cmap='viridis', sides='default', mode='default', scale='dB');
    plt.title('Frequency-Time Plot')

    # 光谱包络图
    plt.subplot(4, 3, 6)
    tempogram = librosa.feature.tempogram(y=y, sr=sr)
    librosa.display.specshow(tempogram, sr=sr, x_axis='time', y_axis='tempo')
    plt.title('Tempogram')

    plt.tight_layout()
    plt.show()


# formGraph(audio_file=audio_file_1)

'''尝试使用aubio库识别音高、节拍'''


def analyze_audio(filename):
    # 加载音频文件
    samplerate, audio = aubio.source(filename)

    # 创建音高识别对象
    pitch_o = aubio.pitch("yin", samplerate)
    pitch_o.set_unit("Hz")
    pitch_o.set_tolerance(0.8)

    # 创建节拍识别对象
    tempo_o = aubio.tempo("default", win_s=512, hop_s=256, samplerate=samplerate)

    # 分析音频
    pitches = []
    beats = []

    while True:
        samples, read = audio()

        # 音高分析
        pitch = pitch_o(samples)[0]
        confidence = pitch_o.get_confidence()
        if confidence > 0.8:
            pitches.append(pitch)

        # 节拍分析
        is_beat = tempo_o(samples)[0]
        if is_beat:
            beats.append(is_beat)

        if read < len(samples):
            break

    return pitches, beats


'''使用audio进行音高检测，我们创建了一个aubio.pitch对象，并使用"yin"算法进行音高检测。
然后，我们打开音频文件，并在一个循环中逐帧读取音频数据，并通过aubio.pitch对象计算当前帧的音高。
如果检测到非零音高值，我们将其转换为MIDI音高编号，并将其添加到midi_pitches列表中'''


def extract_midi_pitches(filename, samplerate=44100, hop_size=512, win_size=4096):
    # 创建 pitch 对象
    pitch_o = aubio.pitch("yin", win_size, hop_size, samplerate)
    pitch_o.set_tolerance(0.8)

    # 打开音频文件
    source = aubio.source(filename, samplerate, hop_size)
    total_frames = 0
    midi_pitches = []

    while True:
        # 读取音频数据
        samples, read = source()

        # 计算当前帧的音高
        pitch = pitch_o(samples)[0]

        # 如果检测到音高
        if pitch != 0:
            # 将音高转换为 MIDI 编号
            midi_pitch = int(round(aubio.freqtomidi(pitch)))
            midi_pitches.append(midi_pitch)

        total_frames += read

        # 如果没有读取到数据，则退出循环
        if read < hop_size:
            break

    return midi_pitches


midi_standard = extract_midi_pitches(str(audio_file_1))
midi_train = extract_midi_pitches(str(audio_file_2))
print(f"标准是{midi_standard}，测试是：{midi_train}")

'''使用Matplotlib库来实现两首歌的音高差异，绘制差异曲线和直方图'''


def plot_pitch_difference(midi_standard, midi_train):
    # 计算音高差异
    pitch_difference = np.array(midi_standard) - np.array(midi_train)

    # 绘制差异曲线
    plt.figure(figsize=(10, 4))
    plt.plot(pitch_difference, color='blue')
    plt.xlabel('帧数')
    plt.ylabel('音高差异')
    plt.title('音高差异曲线')
    plt.show()

    # 绘制差异直方图
    plt.figure(figsize=(8, 6))
    plt.hist(pitch_difference, bins=20, color='green', edgecolor='black')
    plt.xlabel('音高差异')
    plt.ylabel('频数')
    plt.title('音高差异直方图')
    plt.show()


# 假设你已经提取了两首歌的音高并存储在midi_pitches1和midi_pitches2中
# plot_pitch_difference(midi_standard, midi_train)

'''节拍识别'''

audio_file_1 = librosa.load(audio_file_1)
# y存储音频时间序列，sr存储采样率
y, sr = audio_file_1
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
print(' tempo: {:.2f} beats per minute'.format(tempo))
# 分析音频信号并找出可能的节拍位置，这些位置以帧的形式表示，每个帧都对应音频信号中的一个特定时间点
beat_times = librosa.frames_to_time(beat_frames, sr=sr)
print(beat_times)
