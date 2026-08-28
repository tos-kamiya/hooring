# hooring 🎐

[English](README.md) · [日本語](README_ja-JP.md)

そよぐ風に合わせて、涼しげな風鈴の音を鳴らします。

ガラス（江戸風鈴）と金属（鉄風鈴）の音色を加算合成し、風に合わせて不規則な間隔で打ちます。打つ強さと間隔は 1/f ゆらぎで変化します。短冊が風を受け、舌が動く様子に近いです。

## インストール

GitHub から [pipx](https://pipx.pypa.io/) でインストールします。

```console
pipx install git+https://github.com/tos-kamiya/hooring.git
```

これで `hooring` が `PATH` に入ります。更新は `pipx upgrade hooring` です。

再生には `aplay`（ALSA）または `ffplay`（ffmpeg）が必要です。WAV ファイルの書き出しには不要です。

### 開発

リポジトリを clone し、[uv](https://docs.astral.sh/uv/) で仮想環境を用意します。

```console
uv sync
uv run hooring
```

テスト:

```console
uv run pytest
```

## 使い方

```console
hooring
```

鳴り続けます。止めるには `Ctrl+C`。同じ風をもう一度聞くには、表示された `seed=` を `--seed` に渡してください。

```console
# 1 回だけ鳴らす
hooring --once

# そよ風、風鈴 3 つ、45 秒
hooring -d 45 --wind breeze --voices 3

# 金属の音色
hooring --material metal --wind gusty

# WAV ファイルに書き出す（duration を省略すると 30 秒）
hooring -o natsu.wav -d 20 --seed 7

# 音量を半分に（1 が現状の最大）
hooring --volume 0.5
```

### オプション

| フラグ | 意味 |
| --- | --- |
| `-d`, `--duration SEC` | 再生または書き出しの秒数。省略すると鳴り続ける |
| `-o`, `--output FILE` | 再生せず WAV ファイルに書き出す |
| `--seed N` | 乱数シード |
| `--wind breeze\|moderate\|gusty` | 風の強さ |
| `--voices N` | 風鈴の数（1–6、デフォルト 2） |
| `--material glass\|metal\|mixed` | 音色 |
| `--once` | 1 回鳴らして終了 |
| `--mono` | モノラル出力 |
| `--sample-rate HZ` | サンプルレート |
| `--volume GAIN` | 音量 0–1（1 が現状の最大、デフォルト 1） |

Python から:

```python
from hooring import render

audio = render(duration=8, seed=1, wind="breeze", material="glass", volume=0.5)
# ステレオ: shape (n, 2)、float64、範囲 [-1, 1]
```

## リリースノート

→ [Release Notes](release-notes.md)

## ライセンス

`hooring` は [MIT](https://spdx.org/licenses/MIT.html) ライセンスの条件で配布されます。
