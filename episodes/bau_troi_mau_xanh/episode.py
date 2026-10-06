"""Tập 2: Tại sao bầu trời màu xanh?"""
from hh2d import Actor, Cam, Scene

TITLE = "Tại sao bầu trời màu xanh?"
VOICE = dict(voice="thanh_phong", speed=1.4)

BLUE = (70, 150, 255)
ORANGE = (255, 150, 60)

# vị trí các phân tử khí (dùng chung cảnh 5 và 6)
MOLS = [(560, 520), (900, 300), (1180, 560), (1500, 330), (760, 760), (1380, 760), (1700, 600), (300, 330)]

SCENES = [
    # 1. Hook
    Scene(
        say="Bạn có bao giờ tự hỏi: tại sao bầu trời lại có *màu xanh*?",
        bg="troi",
        cam=Cam(zoom=(1.0, 1.08), focus=(1100, 500)),
        actors=[
            Actor("mat_troi", 250, 170, enter="drop", idle="float"),
            Actor("may", 900, 160, enter="slide_right", enter_at=.2, idle="float", move=(-30, 0)),
            Actor("may", 1650, 120, scale=.7, enter="slide_right", enter_at=.4, idle="float", move=(-45, 0)),
            Actor("nguoi_nho", 420, 790, enter="pop", enter_at=.5, idle="hop"),
            Actor("nguoi_nho", 560, 790, enter="pop", enter_at=.65, idle="hop", kw=dict(color=(90, 160, 240))),
            Actor("giao_su", 1150, 620, enter="slide_right", talk=True, idle="breathe", kw=dict(pose="think")),
            Actor("dau_hoi", 1470, 300, enter="pop", enter_at=1.4, idle="wiggle", scale=.8),
        ],
    ),
    # 2. Ánh sáng trắng
    Scene(
        say="Ánh sáng Mặt Trời trông có vẻ màu trắng...",
        fx=["twinkle"],
        cam=Cam(zoom=(1.0, 1.06)),
        dur=3.0,
        actors=[
            Actor("mat_troi", 230, 520, scale=1.6, enter="spin_in", idle="pulse"),
            Actor("tia_sang", 920, 520, enter="fade", enter_dur=.01, enter_at=.5, sound="whoosh",
                  kw=dict(length=1100, grow=1.2)),
            Actor("giao_su", 1700, 640, scale=.7, flip=True, enter="slide_right", enter_at=.2, talk=True,
                  idle="breathe", kw=dict(pose="idle")),
        ],
    ),
    # 3. Lăng kính tách màu
    Scene(
        say="nhưng thật ra, nó là hỗn hợp của *bảy màu cầu vồng*.",
        fx=["twinkle"],
        cam=Cam(zoom=(1.0, 1.1), focus=(960, 500), punch=[1.7]),
        dur=4.0,
        actors=[
            Actor("tia_sang", 450, 560, enter=None, kw=dict(length=780, grow=.5)),
            Actor("lang_kinh", 870, 560, enter="drop", enter_at=.1, idle="sway"),
            Actor("cau_vong", 885, 560, enter="fade", enter_dur=.01, enter_at=.7, sound="whoosh",
                  kw=dict(length=900, spread=.5, grow=1.0)),
            Actor("chu", 1500, 160, enter="pop", enter_at=1.7, idle="pulse",
                  kw=dict(text="7 màu!", size=120, color=(255, 214, 80))),
            Actor("sao", 1250, 140, enter="pop", enter_at=1.9, idle="wiggle"),
        ],
    ),
    # 4. Bước sóng
    Scene(
        say="Mỗi màu là một sóng ánh sáng. Màu đỏ có sóng *dài*, còn màu xanh có sóng *ngắn*.",
        fx=["twinkle"],
        cam=Cam(zoom=(1.0, 1.05)),
        actors=[
            Actor("song", 960, 340, enter="slide_left", enter_at=.3, sound="whoosh",
                  kw=dict(length=1200, wavelength=380, amp=75, color=(235, 70, 60), speed=.8)),
            Actor("chu", 960, 190, enter="pop", enter_at=2.0, idle="bob",
                  kw=dict(text="Đỏ: sóng DÀI", size=64, color=(255, 120, 100))),
            Actor("song", 960, 720, enter="slide_left", enter_at=3.0, sound="whoosh",
                  kw=dict(length=1200, wavelength=110, amp=45, color=BLUE, speed=2.2)),
            Actor("chu", 960, 600, enter="pop", enter_at=3.6, idle="bob",
                  kw=dict(text="Xanh: sóng NGẮN", size=64, color=(120, 190, 255))),
        ],
    ),
    # 5. Phân tử khí
    Scene(
        say="Khi vào bầu khí quyển, ánh sáng va phải vô số *phân tử khí* nhỏ xíu.",
        bg=(150, 205, 245),
        cam=Cam(zoom=(1.0, 1.06)),
        actors=[Actor("phan_tu", x, y, enter="pop", enter_at=.15 * i, idle="float wiggle" if i % 2 else "float")
                for i, (x, y) in enumerate(MOLS)] + [
            Actor("tia_sang", 600, 300, rot=-22, enter="fade", enter_dur=.01, enter_at=1.4, sound="whoosh",
                  kw=dict(length=1100, grow=1.0)),
        ],
    ),
    # 6. Tán xạ
    Scene(
        say="Ánh sáng xanh sóng ngắn bị chúng *bật tung* ra khắp mọi hướng.",
        bg=(150, 205, 245),
        transition="cut",
        cam=Cam(zoom=(1.0, 1.15), focus=(1000, 520), punch=[.4]),
        actors=[Actor("tan_xa", x, y, enter="pop", enter_at=.3 + .12 * i, sound=None,
                      kw=dict(color=BLUE, seed=i * .9)) for i, (x, y) in enumerate(MOLS)] +
               [Actor("phan_tu", x, y, enter=None, idle="wiggle") for x, y in MOLS] + [
            Actor("tia_sang", 960, 440, enter=None, kw=dict(length=2000, grow=0, width=10, color=(240, 90, 70))),
        ],
    ),
    # 7. Cả bầu trời xanh
    Scene(
        say="Vì vậy, dù nhìn về đâu, ta cũng thấy *màu xanh* phủ kín bầu trời!",
        bg="troi",
        fx=[("sparkle", dict(y1=700))],
        cam=Cam(zoom=(1.12, 1.0), pan=((0, -60), (0, 40))),
        actors=[Actor("tan_xa", x, y, scale=.55, enter="pop", enter_at=.1 * i, sound=None,
                      kw=dict(color=BLUE, seed=i)) for i, (x, y) in
                enumerate([(300, 200), (700, 140), (1100, 220), (1500, 150), (1750, 380), (500, 420), (1300, 420)])] + [
            Actor("mat_troi", 1700, 160, scale=.8, enter="pop", idle="float"),
            Actor("giao_su", 960, 600, enter="rise", talk=True, idle="hop", kw=dict(pose="cheer")),
        ],
    ),
    # 8. Tên hiện tượng
    Scene(
        say="Hiện tượng này gọi là *tán xạ Rayleigh*.",
        read="Hiện tượng này gọi là tán xạ Rây lây.",
        fx=["twinkle", ("rays", dict(x=1150, y=420, color=(24, 36, 74), speed=.3)), "sparkle"],
        cam=Cam(zoom=(1.0, 1.08), punch=[.6]),
        dur=3.2,
        actors=[
            Actor("chu", 1150, 420, enter="spin_in", enter_at=.5, enter_dur=.6, idle="pulse",
                  kw=dict(text="Tán xạ\nRayleigh", size=140, color=(120, 190, 255))),
            Actor("giao_su", 380, 640, scale=.8, enter="slide_left", talk=True, idle="breathe", kw=dict(pose="point")),
        ],
    ),
    # 9. Hoàng hôn
    Scene(
        say="Còn lúc hoàng hôn, ánh sáng phải đi xa hơn qua lớp không khí dày...",
        bg="hoang_hon",
        transition="fade",
        cam=Cam(zoom=(1.0, 1.06)),
        actors=[
            Actor("mat_troi", 1550, 300, enter=None, path=[(0, 1550, 300), (5, 1550, 640)],
                  kw=dict(color=(255, 150, 70), ray=(255, 120, 60))),
            Actor("may", 900, 200, scale=.8, enter="slide_left", idle="float", move=(20, 0)),
            Actor("tia_sang", 1000, 660, flip=True, enter="fade", enter_dur=.01, enter_at=1.0, sound="whoosh",
                  kw=dict(length=1000, grow=1.8, color=(255, 230, 190))),
            Actor("giao_su", 330, 620, scale=.85, enter="slide_left", talk=True, idle="breathe", kw=dict(pose="idle")),
        ],
    ),
    # 10. Chỉ còn đỏ cam
    Scene(
        say="nên màu xanh bị tán xạ hết trên đường, chỉ còn *đỏ và cam* đến được mắt ta.",
        bg="hoang_hon",
        cam=Cam(zoom=(1.0, 1.1), focus=(700, 600), punch=[3.2]),
        actors=[
            Actor("mat_troi", 1550, 640, enter=None, kw=dict(color=(255, 150, 70), ray=(255, 120, 60))),
            Actor("tan_xa", 1100, 560, enter="pop", enter_at=.3, kw=dict(color=BLUE, reach=150)),
            Actor("tan_xa", 850, 620, enter="pop", enter_at=.6, kw=dict(color=BLUE, reach=130, seed=1.3)),
            Actor("tia_sang", 1000, 640, flip=True, enter="fade", enter_dur=.01, enter_at=1.4, sound="whoosh",
                  kw=dict(length=1000, grow=1.2, width=16, color=(240, 70, 50))),
            Actor("tia_sang", 1000, 690, flip=True, enter="fade", enter_dur=.01, enter_at=1.7, sound=None,
                  kw=dict(length=1000, grow=1.2, width=16, color=ORANGE)),
            Actor("giao_su", 330, 620, scale=.85, enter=None, talk=True, idle="breathe",
                  kw=dict(pose="wave")),
        ],
    ),
    # 11. Kết
    Scene(
        say="Giờ thì bạn đã biết rồi đấy! Đăng ký kênh để xem thêm nhé!",
        bg="troi",
        fx=[("confetti", dict(seed=5))],
        cam=Cam(zoom=(1.08, 1.0)),
        dur=5.5,
        actors=[
            Actor("mat_troi", 260, 180, enter="pop", idle="float"),
            Actor("giao_su", 900, 600, enter="rise", talk=True, idle="hop", kw=dict(pose="cheer")),
            Actor("nut_dang_ky", 1500, 420, enter="pop", enter_at=2.4, idle="pulse"),
            Actor("sao", 1700, 290, enter="pop", enter_at=2.7, idle="wiggle"),
            Actor("sao", 1320, 300, enter="pop", enter_at=2.9, idle="wiggle", kw=dict(r=16)),
        ],
    ),
]
