# VVT Hoạt Hình 2D

Làm video hoạt hình 2D vẽ tay kiểu "người que giải thích" (faceless YouTube) **tự động và free**:

**kịch bản (episode.py) → giọng KorvaTTS → hoạt cảnh nhiều chuyển động → phụ đề + âm thanh → mp4**

Không cần biết dựng phim. Mỗi câu thoại là một cảnh. Trong cảnh, nhân vật/đồ vật tự bay vào, nảy, lắc, quay, nhép miệng theo giọng. Camera tự zoom, giật nhịp, rung, chuyển cảnh lia nhanh. Phụ đề chữ viết tay hiện theo giọng đọc, từ khoá tô vàng. Hiệu ứng tiếng pop/vút/bùm tự chèn.

## Cài đặt (làm 1 lần)

```bash
pip install -r requirements.txt
# cài ffmpeg và cho vào PATH (Windows: winget install ffmpeg)
```

Giọng đọc tự chọn theo thứ tự: **KorvaTTS `thanh_phong`** (giống repo vvt-tin-tuc, máy Đại Ca đã có ở `F:\AI_WORK\KORVATTS`, tool tự nhận) → **edge-tts** (free, cần mạng) → **espeak-ng** (robot, chỉ để test).
Ép engine: thêm `--tts korva` / `--tts edge`.

### Giọng làm sẵn trên máy khác (`giong/`)

Máy nào không chạy được KorvaTTS (vd Claude trên cloud) vẫn dùng được giọng thật: máy có KorvaTTS chạy
`python -m hh2d.voice --all` rồi commit + push thư mục `giong/` (file .flac). Khi dựng, tool tự lấy giọng trong `giong/` trước.

## Dựng video

```bash
python -m hh2d.build episodes/trai_dat_ngung_quay                       # ra episodes/.../out/*.mp4
python -m hh2d.build episodes/trai_dat_ngung_quay --res 1280x720         # xem nhanh
python -m hh2d.build episodes/trai_dat_ngung_quay --scenes 3-5           # chỉ dựng cảnh 3 đến 5
python -m hh2d.build episodes/trai_dat_ngung_quay --still 5 12.5         # xuất ảnh tĩnh để soi
python -m hh2d.build episodes/trai_dat_ngung_quay --music nhac.mp3       # thêm nhạc nền (tự hạ khi có giọng)
python -m hh2d.build episodes/trai_dat_ngung_quay --short                # Short dọc 9:16 (tiêu đề trên, phụ đề dưới)
python -m hh2d.build episodes/video_dai_01                               # video dài gom nhiều tập
```

## Short + video dài

- Mỗi chủ đề là một tập (~40-60s). Xuất Short bằng `--short`. Cảnh nào bị cắt mất vật khi dọc thì thêm `short_x=...` (tâm khung) cho cảnh đó.
- Cảnh kết "Đăng ký kênh" đánh dấu `outro=True`: có trong Short, tự bỏ khi gom.
- Video dài: `episodes/video_dai_01/episode.py`, thêm tên tập vào danh sách `TAP`. Mỗi tập tự có thẻ "Câu hỏi #k" ở đầu, có sẵn cảnh mở đầu và kết. 12-14 tập ≈ 9-11 phút.

Tập mẫu 34 giây (1080p) dựng mất khoảng 1 phút trên máy 4 nhân. Giọng được cache, sửa hình không phải đọc lại.

## Viết một tập mới

Tạo `episodes/<ten_tap>/episode.py` (chép từ tập mẫu):

```python
from hh2d import Actor, Cam, Scene

TITLE = "Nếu Trái Đất ngừng quay 1 giây?"
VOICE = dict(voice="thanh_phong", speed=1.4)

SCENES = [
    Scene(
        say="Hiện tại, Trái Đất quay với tốc độ *1.670 km/h*.",          # phụ đề, *từ khoá* tô vàng
        read="Hiện tại, Trái Đất quay với tốc độ một nghìn sáu trăm bảy mươi ki lô mét một giờ.",  # lời đọc (nếu khác)
        bg="vu_tru",
        fx=["twinkle", ("rays", dict(x=900, y=560))],
        cam=Cam(zoom=(1.0, 1.1), punch=[2.6]),
        actors=[
            Actor("trai_dat", 900, 580, enter="spin_in", kw=dict(r=320, spin=1.6)),
            Actor("chu", 900, 120, enter="pop", enter_at=2.6, idle="pulse",
                  kw=dict(text="1.670 km/h", size=120, color=(255, 110, 80))),
            Actor("giao_su", 1620, 640, scale=.75, flip=True, enter="slide_right",
                  talk=True, kw=dict(pose="point")),
        ],
    ),
]
```

Toạ độ luôn theo khung **1920x1080** (x: trái→phải, y: trên→dưới, là tâm của vật). Vật nào khai báo sau thì nằm trên.

### Actor: chuyển động

| Tham số | Giá trị |
|---|---|
| `enter` | `pop` `slide_left` `slide_right` `drop` (rơi nảy) `rise` `fade` `spin_in` `grow` `None` |
| `enter_at`, `enter_dur` | giây bắt đầu xuất hiện, thời gian xuất hiện |
| `exit`, `exit_at` | `pop` `slide_left` `slide_right` `fall` `rise` `fade` `spin_out` — `exit_at` âm = tính từ cuối cảnh |
| `idle` | chuyển động liên tục, ghép bằng dấu cách: `bob` `float` `sway` `wiggle` `breathe` `pulse` `hop` `shake` `jelly` |
| `path` | `[(giây, x, y), ...]` đi mượt qua các điểm |
| `move`, `gravity`, `spin` | bay thẳng (px/s), rơi (px/s²), xoay (độ/s): dùng cho đồ bị hất văng |
| `talk=True` | nhép miệng + nhún theo giọng đọc |
| `flip`, `scale`, `rot` | lật ngang, phóng to, nghiêng |
| `sound` | `auto` (tự chọn theo enter) `pop` `whoosh` `ding` `boom` `None` |

### Hình vẽ sẵn (không cần API ảnh)

- `giao_su`: ông giáo sư người que. `kw=dict(pose=..., face=...)`. pose: `idle` `point` `wave` `shock` `shrug` `fly` `cheer` `think`. face: `smile` `shock` `sad`.
- `nguoi_nho` (dân thường, `color=`), `trai_dat` (`r`, `spin`, `stop_at`, `face="happy"/"scared"`), `hanh_tinh`, `mat_troi`, `sao`, `may`
- `nha`, `cay`, `o_to`, `con_bo`, `may_bay`, `bien_stop`, `nut_dang_ky`, `mui_ten`, `mui_ten_cong`, `dau_hoi`, `vu_no`
- `chu`: chữ viết tay to, `kw=dict(text="...", size=120, color=(r,g,b))`

Thêm hình mới: viết hàm trong `hh2d/doodles.py` (hoặc ngay trong episode.py) với `@doodle(rong, cao)`.

### Scene, nền, hiệu ứng, camera

- `bg`: `vu_tru` `giay` `troi` `(r,g,b)` hoặc `img:ten_anh` (ảnh trong `images/` của tập)
- `fx`: `twinkle` (sao nhấp nháy), `speed` (vệt tốc độ), `confetti`, `sparkle`, `("rays", {...})` (tia xoay), `("flash", {"t": 1.0})` (loé trắng + tiếng bùm)
- `cam=Cam(zoom=(a, b), pan=((x0,y0),(x1,y1)), punch=[giây], shake=[(giây, dài, biên_độ)], focus=(x, y))`
- `transition`: chuyển vào cảnh: `whip` (lia nhanh, mặc định) `zoom` `fade` `cut`
- `dur`: thời lượng tối thiểu nếu cần chờ hoạt cảnh dài hơn câu đọc. `sfx=[(giây, "boom")]`: tiếng thêm.

## Dùng ảnh AI (đẹp hơn, vẫn free)

1. Tạo ảnh nhân vật/đồ vật trên **Gemini web** (hoặc Bing Image Creator) với nền trắng. Prompt mẫu:
   `A cute white stick figure scientist, round head, dot eyes, white lab coat, plaid shirt, hand-drawn doodle, colored pencil texture, thick black outlines, full body, plain pure white background`
2. Lưu vào `episodes/<tap>/images/ten.png`, rồi tách nền: `python -m hh2d.images --cutout episodes/<tap>/images/ten.png`
3. Dùng: `Actor("img:ten", 500, 600, width=420, idle="bob")`. Ảnh cũng được rung nét, nảy, xoay, bay như hình vẽ sẵn.

**Tự động bằng API** (cần `GEMINI_API_KEY` lấy ở https://aistudio.google.com/apikey): khai báo `STYLE`, `CHARACTER`, `IMAGES` trong episode.py (xem đầu file `hh2d/images.py`) rồi chạy `python -m hh2d.images episodes/<tap>`.

## Cấu trúc

```
hh2d/draw.py      nét vẽ tay (đường rung, tô bút chì, chữ)
hh2d/doodles.py   thư viện hình vẽ sẵn
hh2d/scene.py     Scene / Actor / Cam + chuyển động
hh2d/render.py    dựng khung hình, camera, chuyển cảnh, phụ đề
hh2d/audio.py     giọng đọc, hiệu ứng tiếng, trộn nhạc
hh2d/images.py    ảnh AI + tách nền
hh2d/build.py     lệnh dựng
episodes/         mỗi tập một thư mục (out/ và cache/ không đưa lên repo)
fonts/            Patrick Hand (SIL OFL)
```
