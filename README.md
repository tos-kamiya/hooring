# hooring

風まかせに、涼しげな風鈴の音を鳴らします。

ガラス（江戸風鈴）と金属（鉄風鈴）の音色を加算合成し、そよ風の強さに応じて不規則に打ちます。短冊が風を受けて舌を動かす、あの間をイメージしています。

## インストール

[uv](https://docs.astral.sh/uv/) で仮想環境と依存関係を揃えます。

```console
uv sync
uv run hooring
```

テスト:

```console
uv run pytest
```

パッケージとして入れる場合:

```console
uv pip install hooring
```

再生には `aplay`（ALSA）か `ffplay`（ffmpeg）が必要です。WAV への書き出しだけなら不要です。

## 使い方

```console
hooring
```

鳴り続けます。`Ctrl+C` で止めます。同じ風をもう一度聞くには、表示された `seed=` を `--seed` に渡してください。

```console
# 一打だけ
hooring --once

# そよ風、風鈴は3つ、45秒
hooring -d 45 --wind breeze --voices 3

# 金属の音色
hooring --material metal --wind gusty

# WAV に書き出す（秒数省略時は 30 秒）
hooring -o natsu.wav -d 20 --seed 7
```

### オプション

| フラグ | 意味 |
| --- | --- |
| `-d`, `--duration SEC` | 再生または書き出し秒数。省略時は鳴り続ける |
| `-o`, `--output FILE` | WAV へ書き出す（再生しない） |
| `--seed N` | 乱数シード |
| `--wind breeze\|moderate\|gusty` | 風の強さ |
| `--voices N` | 風鈴の数（1–6、default 2） |
| `--material glass\|metal\|mixed` | 音色 |
| `--once` | 一打だけ鳴らして終わる |
| `--mono` | モノラル出力 |
| `--sample-rate HZ` | サンプリング周波数 |

Python から:

```python
from hooring import render

audio = render(duration=8, seed=1, wind="breeze", material="glass")
# stereo: shape (n, 2), float64 in [-1, 1]
```

## License

`hooring` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
